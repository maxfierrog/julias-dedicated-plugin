/* Home screen widgets: edit mode (remove, drag to reorder, add from the
   catalog) and the Timeline's add-event form. Layout changes are saved as
   the ordered list of widget ids in her settings (home.widgets). */
(function () {
  "use strict";

  let editing = false;
  let dragging = null;

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const grid = () => $(".jdp-grid");
  const catalog = () => $("#jdp-catalog");

  function save() {
    const order = $$(".jdp-grid > .jdp-widget").map(
      (w) => `${w.dataset.id}:${w.dataset.size}`,
    );
    pycmd("jdp:set:" + JSON.stringify(["home.widgets", order]));
  }

  function sizeLabel(w) {
    const sizes = w.dataset.sizes.split(",").map((x) => x.replace("x", "×"));
    return sizes.length > 1 ? sizes.join(" · ") : sizes[0];
  }

  // Re-render the page (fresh content at a new size) without leaving edit
  // mode; the flag survives the reload.
  function rerenderEditing() {
    try {
      sessionStorage.setItem("jdp-editing", "1");
    } catch (e) {}
    pycmd("decks");
  }

  // ---- Resize: drag the corner handle; snaps to the widget's sizes ------
  function slot() {
    const g = grid();
    const cs = getComputedStyle(g);
    const gap = parseFloat(cs.columnGap) || 0;
    const colW = (g.clientWidth - gap * 2) / 3;
    const rowH = parseFloat(cs.gridAutoRows) || 152;
    return { colW, rowH: Math.max(rowH, 140), gap };
  }

  function setSize(w, size) {
    const [c, r] = size.split("x");
    w.classList.remove("jdp-cols-1", "jdp-cols-2", "jdp-cols-3", "jdp-rows-1", "jdp-rows-2");
    w.classList.add(`jdp-cols-${c}`, `jdp-rows-${r}`);
    w.dataset.size = size;
  }

  function startResize(e, w) {
    e.preventDefault();
    e.stopPropagation();
    const sizes = w.dataset.sizes.split(",");
    const start = w.dataset.size;
    const rect = w.getBoundingClientRect();
    const { colW, gap } = slot();
    const rowH = rect.height / Number(start.split("x")[1]);
    w.draggable = false;
    w.classList.add("jdp-resizing");
    const move = (ev) => {
      const wantC = (rect.width + ev.clientX - e.clientX + gap) / (colW + gap);
      const wantR = (rect.height + ev.clientY - e.clientY + gap) / (rowH + gap);
      let best = start;
      let bestD = Infinity;
      for (const s of sizes) {
        const [c, r] = s.split("x").map(Number);
        const d = Math.abs(c - wantC) + Math.abs(r - wantR);
        if (d < bestD) [best, bestD] = [s, d];
      }
      if (best !== w.dataset.size) setSize(w, best);
    };
    const up = () => {
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerup", up);
      w.classList.remove("jdp-resizing");
      w.draggable = true;
      if (w.dataset.size !== start) {
        save();
        rerenderEditing();
      }
    };
    document.addEventListener("pointermove", move);
    document.addEventListener("pointerup", up);
  }

  // ---- Edit mode -------------------------------------------------------
  function decorate(w) {
    w.draggable = true;
    if (!$(".jdp-w-remove", w)) {
      const x = document.createElement("button");
      x.type = "button";
      x.className = "jdp-w-remove";
      x.title = "Remove widget";
      x.setAttribute("aria-label", "Remove " + w.dataset.name);
      x.textContent = "×";
      x.addEventListener("click", (e) => {
        e.stopPropagation();
        undecorate(w);
        catalog().content.appendChild(w);
        save();
        renderPicker();
      });
      w.appendChild(x);
    }
    if (w.dataset.sizes.includes(",") && !$(".jdp-w-resize", w)) {
      const h = document.createElement("span");
      h.className = "jdp-w-resize";
      h.title = "Drag to resize";
      h.addEventListener("pointerdown", (e) => startResize(e, w));
      w.appendChild(h);
    }
  }

  function undecorate(w) {
    w.draggable = false;
    $(".jdp-w-remove", w)?.remove();
    $(".jdp-w-resize", w)?.remove();
  }

  function renderPicker() {
    let picker = $(".jdp-picker");
    const items = [...catalog().content.children];
    if (!picker) {
      picker = document.createElement("div");
      picker.className = "jdp-picker";
      $(".jdp-edit-bar").before(picker);
    }
    picker.replaceChildren();
    const h = document.createElement("h4");
    h.textContent = items.length ? "Add a widget" : "Every widget is on your home screen";
    picker.appendChild(h);
    const list = document.createElement("div");
    list.className = "jdp-picker-list";
    for (const w of items) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "jdp-picker-item";
      b.innerHTML =
        "<span class='jdp-picker-name'></span><span class='jdp-picker-size'></span>" +
        "<span class='jdp-picker-desc'></span>";
      $(".jdp-picker-name", b).textContent = w.dataset.name;
      $(".jdp-picker-size", b).textContent = sizeLabel(w);
      $(".jdp-picker-desc", b).textContent = w.dataset.desc;
      b.addEventListener("click", () => {
        grid().appendChild(w);
        decorate(w);
        save();
        renderPicker();
        w.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
      list.appendChild(b);
    }
    picker.appendChild(list);
  }

  function setEditing(on) {
    editing = on;
    document.documentElement.classList.toggle("jdp-editing", on);
    const btn = $(".jdp-edit-toggle");
    btn.textContent = on ? "Done" : "Edit widgets";
    btn.classList.toggle("jdp-primary", on);
    $$(".jdp-grid > .jdp-widget").forEach(on ? decorate : undecorate);
    if (on) {
      renderPicker();
    } else {
      $(".jdp-picker")?.remove();
      try {
        sessionStorage.removeItem("jdp-editing");
      } catch (e) {}
      pycmd("decks"); // re-render with fresh data for newly added widgets
    }
  }

  // ---- Drag to reorder -------------------------------------------------
  function onDragStart(e) {
    const w = e.target.closest?.(".jdp-widget");
    if (!editing || !w) return;
    dragging = w;
    w.classList.add("jdp-dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", w.dataset.id);
  }

  function onDragOver(e) {
    if (!dragging) return;
    e.preventDefault();
    const target = e.target.closest?.(".jdp-grid > .jdp-widget");
    if (!target || target === dragging) return;
    const r = target.getBoundingClientRect();
    const after = e.clientX > r.left + r.width / 2;
    target[after ? "after" : "before"](dragging);
  }

  function onDragEnd() {
    if (!dragging) return;
    dragging.classList.remove("jdp-dragging");
    dragging = null;
    save();
  }

  // ---- Timeline form ---------------------------------------------------
  function onClick(e) {
    const t = e.target;
    if (t.closest(".jdp-edit-toggle")) {
      setEditing(!editing);
    } else if (t.closest(".jdp-tl-add")) {
      const form = $(".jdp-tl-form", t.closest(".jdp-timeline"));
      form.hidden = false;
      $("input[name=title]", form).focus();
    } else if (t.closest(".jdp-tl-cancel")) {
      t.closest(".jdp-tl-form").hidden = true;
    }
  }

  function onSubmit(e) {
    const form = e.target.closest(".jdp-tl-form");
    if (!form) return;
    e.preventDefault();
    const title = form.title.value.trim();
    const date = form.date.value;
    const deck = form.deck ? form.deck.value : "";
    if (title && date) {
      pycmd("jdp:event-add:" + JSON.stringify({ title, date, deck }));
    }
  }

  // Countdown labels that would collide with the previous one are hidden
  // (the event's details still show on hover).
  function tidyTimeline() {
    let lastRight = -Infinity;
    $$(".jdp-tl-count").forEach((c) => {
      c.style.visibility = "";
      const r = c.getBoundingClientRect();
      if (r.left < lastRight + 6) c.style.visibility = "hidden";
      else lastRight = r.right;
    });
  }

  // "No more items" notes only show when the list leaves a lot of space.
  function tidyListEnds() {
    $$(".jdp-list-end").forEach((el) => {
      el.classList.toggle("jdp-hidden", el.clientHeight < 64);
    });
  }

  function init() {
    if (!grid()) return;
    tidyTimeline();
    tidyListEnds();
    window.addEventListener("resize", tidyListEnds);
    window.addEventListener("resize", tidyTimeline);
    document.addEventListener("click", onClick);
    document.addEventListener("submit", onSubmit);
    document.addEventListener("dragstart", onDragStart);
    document.addEventListener("dragover", onDragOver);
    document.addEventListener("dragend", onDragEnd);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && editing) setEditing(false);
    });
    let resume = false;
    try {
      resume = sessionStorage.getItem("jdp-editing") === "1";
    } catch (e) {}
    if (resume) {
      editing = true;
      document.documentElement.classList.add("jdp-editing");
      const btn = $(".jdp-edit-toggle");
      btn.textContent = "Done";
      btn.classList.add("jdp-primary");
      $$(".jdp-grid > .jdp-widget").forEach(decorate);
      renderPicker();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

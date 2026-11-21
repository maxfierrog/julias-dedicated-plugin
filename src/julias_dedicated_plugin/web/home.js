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
    pycmd("jdp:home-refresh");
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

  function sizeLabels(w) {
    const out = {};
    (w.dataset.labels || "").split(";").filter(Boolean).forEach((pair) => {
      const [size, label] = pair.split("=");
      out[size] = label;
    });
    return out;
  }

  // Which directions this widget can be resized in.
  function axes(w) {
    const sizes = w.dataset.sizes.split(",").map((x) => x.split("x").map(Number));
    return {
      h: new Set(sizes.map((s) => s[0])).size > 1,
      v: new Set(sizes.map((s) => s[1])).size > 1,
    };
  }

  function startResize(e, w, axis) {
    e.preventDefault();
    e.stopPropagation();
    const start = w.dataset.size;
    const [c0, r0] = start.split("x").map(Number);
    const sizes = w.dataset.sizes
      .split(",")
      .filter((s) => (axis === "h" ? Number(s.split("x")[1]) === r0 : Number(s.split("x")[0]) === c0));
    const labels = sizeLabels(w);
    const rect = w.getBoundingClientRect();
    const { colW, gap } = slot();
    const rowH = (rect.height - gap * (r0 - 1)) / r0;
    w.classList.add("jdp-resizing");
    const badge = document.createElement("span");
    badge.className = "jdp-w-badge";
    badge.textContent = labels[start] || start.replace("x", " × ");
    w.appendChild(badge);
    document.documentElement.style.cursor = axis === "h" ? "ew-resize" : "ns-resize";

    const move = (ev) => {
      let best = start;
      let bestD = Infinity;
      for (const s of sizes) {
        const [c, r] = s.split("x").map(Number);
        const d =
          axis === "h"
            ? Math.abs(rect.width + (ev.clientX - e.clientX) - (c * colW + (c - 1) * gap))
            : Math.abs(rect.height + (ev.clientY - e.clientY) - (r * rowH + (r - 1) * gap));
        if (d < bestD) [best, bestD] = [s, d];
      }
      if (best !== w.dataset.size) {
        setSize(w, best);
        badge.textContent = labels[best] || best.replace("x", " × ");
      }
    };
    const up = () => {
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerup", up);
      document.documentElement.style.cursor = "";
      w.classList.remove("jdp-resizing");
      badge.remove();
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
    const can = axes(w);
    for (const axis of ["h", "v"]) {
      if (!can[axis] || $(`.jdp-w-handle.jdp-${axis}`, w)) continue;
      const h = document.createElement("span");
      h.className = `jdp-w-handle jdp-${axis}`;
      h.title = axis === "h" ? "Drag to make wider or narrower" : "Drag to make taller or shorter";
      h.addEventListener("pointerdown", (e) => startResize(e, w, axis));
      w.appendChild(h);
    }
  }

  function undecorate(w) {
    $(".jdp-w-remove", w)?.remove();
    $$(".jdp-w-handle", w).forEach((h) => h.remove());
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
      pycmd("jdp:home-refresh"); // re-render with fresh data for newly added widgets
    }
  }

  // ---- Drag to reorder ---------------------------------------------------
  // Pointer events (Anki's web views reject HTML5 drag-and-drop): a floating
  // copy follows the pointer, the widget's own slot stays as a placeholder,
  // and the others slide out of the way (FLIP animation).
  const DRAG_THRESHOLD = 6;
  let pending = null; // { w, x, y } before the threshold is passed
  let drag = null; // { w, ghost, dx, dy }

  function flip(mutate) {
    const items = $$(".jdp-grid > .jdp-widget");
    const before = new Map(items.map((el) => [el, el.getBoundingClientRect()]));
    mutate();
    for (const el of items) {
      if (drag && el === drag.w) continue;
      const a = before.get(el);
      const b = el.getBoundingClientRect();
      const dx = a.left - b.left;
      const dy = a.top - b.top;
      if (!dx && !dy) continue;
      el.animate(
        [{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "none" }],
        { duration: 180, easing: "cubic-bezier(0.2, 0.8, 0.2, 1)" },
      );
    }
  }

  function onPointerDown(e) {
    if (!editing || e.button !== 0) return;
    if (e.target.closest(".jdp-w-handle, .jdp-w-remove, button, input, select")) return;
    const w = e.target.closest(".jdp-grid > .jdp-widget");
    if (!w) return;
    pending = { w, x: e.clientX, y: e.clientY };
  }

  function startDrag(e) {
    const { w } = pending;
    pending = null;
    const r = w.getBoundingClientRect();
    const ghost = w.cloneNode(true);
    ghost.classList.add("jdp-ghost");
    $$(".jdp-w-handle, .jdp-w-remove", ghost).forEach((x) => x.remove());
    Object.assign(ghost.style, {
      width: r.width + "px",
      height: r.height + "px",
      left: r.left + "px",
      top: r.top + "px",
    });
    document.body.appendChild(ghost);
    w.classList.add("jdp-placeholder");
    document.documentElement.classList.add("jdp-reordering");
    drag = { w, ghost, dx: e.clientX - r.left, dy: e.clientY - r.top };
  }

  function onPointerMove(e) {
    if (pending) {
      const moved = Math.hypot(e.clientX - pending.x, e.clientY - pending.y);
      if (moved < DRAG_THRESHOLD) return;
      startDrag(e);
    }
    if (!drag) return;
    e.preventDefault();
    drag.ghost.style.left = e.clientX - drag.dx + "px";
    drag.ghost.style.top = e.clientY - drag.dy + "px";
    // Which widget is under the pointer (ignoring the ghost)?
    const under = document.elementFromPoint(e.clientX, e.clientY);
    const target = under?.closest(".jdp-grid > .jdp-widget");
    if (!target || target === drag.w) return;
    const r = target.getBoundingClientRect();
    const after =
      e.clientY > r.bottom - r.height / 4 ||
      (e.clientX > r.left + r.width / 2 && e.clientY > r.top + r.height / 4);
    const ref = after ? target.nextElementSibling : target;
    if (ref === drag.w || (after && target.nextElementSibling === drag.w)) return;
    flip(() => grid().insertBefore(drag.w, ref));
  }

  function onPointerUp() {
    pending = null;
    if (!drag) return;
    const { w, ghost } = drag;
    const to = w.getBoundingClientRect();
    ghost
      .animate(
        [
          { left: ghost.style.left, top: ghost.style.top },
          { left: to.left + "px", top: to.top + "px" },
        ],
        { duration: 160, easing: "ease-out" },
      )
      .finished.finally(() => {
        ghost.remove();
        w.classList.remove("jdp-placeholder");
      });
    document.documentElement.classList.remove("jdp-reordering");
    drag = null;
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
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
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

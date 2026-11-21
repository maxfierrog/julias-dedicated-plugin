/* Deck list: a chevron expander centered on each row, and a fixed-size
   "Today" column with a progress ring (data from Python, set as
   window.JDP_DECK_PROGRESS = {deckId: [done, remaining]}). */
(function () {
  "use strict";

  const CHEVRON =
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" ' +
    'stroke="currentColor" stroke-width="2.6" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';

  function rebuild(row) {
    const cell = row.querySelector("td.decktd");
    if (!cell || cell.querySelector(".jdp-deckcell")) return;
    const name = cell.querySelector("a.deck");
    const toggle = cell.querySelector(".collapse");
    // Anki indents subdecks with six &nbsp; per level.
    const nbsp = (cell.textContent.match(/^ */) || [""])[0].length;
    const level = Math.round(nbsp / 6);

    const wrap = document.createElement("div");
    wrap.className = "jdp-deckcell";
    wrap.style.paddingLeft = level * 22 + "px";

    if (toggle && toggle.tagName === "A") {
      const open = toggle.textContent.trim() !== "+";
      toggle.classList.add("jdp-chevron");
      toggle.classList.toggle("jdp-open", open);
      toggle.setAttribute("aria-label", open ? "Collapse" : "Expand");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.innerHTML = CHEVRON;
      wrap.appendChild(toggle);
    } else {
      const spacer = document.createElement("span");
      spacer.className = "jdp-chevron jdp-spacer";
      wrap.appendChild(spacer);
    }

    const stack = document.createElement("div");
    stack.className = "jdp-deckname";
    if (name) stack.appendChild(name);
    wrap.appendChild(stack);

    cell.replaceChildren(wrap);
  }

  function ring(done, remaining) {
    const total = done + remaining;
    const frac = total ? done / total : 0;
    const r = 7;
    const c = 2 * Math.PI * r;
    const finished = remaining === 0;
    const wrap = document.createElement("span");
    wrap.className = "jdp-today" + (finished ? " jdp-done" : "");
    wrap.title = `${done} of ${total} done today`;
    wrap.innerHTML =
      `<svg viewBox="0 0 18 18" width="18" height="18" aria-hidden="true">` +
      `<circle cx="9" cy="9" r="${r}" class="jdp-ring-bg"/>` +
      `<circle cx="9" cy="9" r="${r}" class="jdp-ring" ` +
      `stroke-dasharray="${(frac * c).toFixed(2)} ${c.toFixed(2)}" ` +
      `transform="rotate(-90 9 9)"/>` +
      (finished
        ? `<path d="M5.6 9.2l2.2 2.1 4.4-4.6" class="jdp-check"/>`
        : "") +
      `</svg><span>${Math.round(frac * 100)}%</span>`;
    return wrap;
  }

  function addTodayColumn() {
    const head = document.querySelector("th.optscol");
    if (!head || document.querySelector("th.jdp-today-col")) return;
    const th = document.createElement("th");
    th.className = "count jdp-today-col";
    th.textContent = "Today";
    head.before(th);
    document.querySelectorAll(".top-level-drag-row td").forEach((td) => {
      td.colSpan = (td.colSpan || 1) + 1;
    });
    const data = window.JDP_DECK_PROGRESS || {};
    document.querySelectorAll("tr.deck").forEach((row) => {
      const opts = row.querySelector("td.opts");
      if (!opts) return;
      const td = document.createElement("td");
      td.className = "jdp-today-cell";
      const p = data[row.id];
      if (p && p[0]) td.appendChild(ring(p[0], p[1]));
      opts.before(td);
    });
  }

  function go() {
    document.querySelectorAll("tr.deck").forEach(rebuild);
    addTodayColumn();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", go);
  } else {
    go();
  }
})();

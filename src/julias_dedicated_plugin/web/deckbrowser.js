/* Deck list rows: a chevron expander centered on the whole item, and a thin
   "today" progress line under the deck name (data from Python, set as
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

    const p = (window.JDP_DECK_PROGRESS || {})[row.id];
    if (p && p[0]) {
      const total = p[0] + p[1];
      const bar = document.createElement("div");
      bar.className = "jdp-deckbar" + (p[1] === 0 ? " jdp-done" : "");
      bar.title = `${p[0]} of ${total} done today`;
      const fill = document.createElement("i");
      fill.style.width = Math.round((100 * p[0]) / total) + "%";
      bar.appendChild(fill);
      stack.appendChild(bar);
    }
    cell.replaceChildren(wrap);
  }

  function go() {
    document.querySelectorAll("tr.deck").forEach(rebuild);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", go);
  } else {
    go();
  }
})();

/* Readable cards: per-card adjustments after Anki renders each side.
   Anki resets its onUpdateHook list on every card, so we watch #qa for
   content changes instead. */
(function () {
  "use strict";

  // Short cards read best centered; paragraphs and lists read best aligned
  // to the start of the line (left, or right in RTL scripts).
  function align(qa) {
    const root = document.documentElement;
    qa.classList.remove("jdp-left");
    if (root.classList.contains("jdp-align-left")) {
      qa.classList.add("jdp-left");
      return;
    }
    if (!root.classList.contains("jdp-align-auto")) return;
    const text = (qa.innerText || "").trim();
    const long = text.length > 260 || qa.querySelector("ul, ol, p + p");
    if (long) qa.classList.add("jdp-left");
  }

  // ---- Click-to-zoom images ---------------------------------------------
  function closeZoom() {
    document.getElementById("jdp-zoom")?.remove();
  }

  function zoom(img) {
    closeZoom();
    const overlay = document.createElement("div");
    overlay.id = "jdp-zoom";
    const big = document.createElement("img");
    big.src = img.src;
    overlay.appendChild(big);
    overlay.addEventListener("click", closeZoom);
    document.body.appendChild(overlay);
  }

  // Any key closes the zoom (Esc without letting Anki also act on it), so
  // answering with Space/1-4 never leaves an old image over the next card.
  document.addEventListener(
    "keydown",
    (e) => {
      if (!document.getElementById("jdp-zoom")) return;
      if (e.key === "Escape") e.stopPropagation();
      closeZoom();
    },
    true,
  );

  document.addEventListener("click", (e) => {
    if (e.defaultPrevented) return; // the note type handled it
    if (!document.documentElement.classList.contains("jdp-cards")) return;
    const img = e.target.closest && e.target.closest("#qa img");
    if (!img) return;
    // Linked or interactive images keep their own behaviour; tiny icons
    // aren't worth zooming.
    if (img.closest("a, button, [onclick], [role=button]")) return;
    if (img.naturalWidth && img.naturalWidth < 48) return;
    e.preventDefault();
    zoom(img);
  });

  // ---- Per-card updates ----------------------------------------------------
  function update() {
    const qa = document.getElementById("qa");
    if (qa) align(qa);
  }

  function watch() {
    const qa = document.getElementById("qa");
    if (!qa) return;
    new MutationObserver(() => {
      closeZoom();
      update();
    }).observe(qa, { childList: true });
    update();
  }

  document.addEventListener("jdp:settings", update);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", watch);
  } else {
    watch();
  }
})();

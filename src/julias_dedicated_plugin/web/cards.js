/* Readable cards: per-card adjustments run after Anki renders each side. */
(function () {
  "use strict";

  // Short cards read best centered; paragraphs and lists read best left.
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

  function zoom(img) {
    const overlay = document.createElement("div");
    overlay.id = "jdp-zoom";
    const big = document.createElement("img");
    big.src = img.src;
    overlay.appendChild(big);
    const close = () => {
      overlay.remove();
      document.removeEventListener("keydown", onKey, true);
    };
    const onKey = (e) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        close();
      }
    };
    overlay.addEventListener("click", close);
    document.addEventListener("keydown", onKey, true);
    document.body.appendChild(overlay);
  }

  document.addEventListener("click", (e) => {
    const img = e.target.closest && e.target.closest("#qa img");
    if (img && document.documentElement.classList.contains("jdp-cards")) {
      e.preventDefault();
      zoom(img);
    }
  });

  function update() {
    const qa = document.getElementById("qa");
    if (qa) align(qa);
  }

  if (window.onUpdateHook) onUpdateHook.push(update);
  document.addEventListener("jdp:settings", update);
})();

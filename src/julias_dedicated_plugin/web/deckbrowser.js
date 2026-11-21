/* Deck list: a quick "Study" button on rows that have cards due, so a deck
   can be started without going through its overview screen. */
(function () {
  "use strict";
  function decorate() {
    document.querySelectorAll("tr.deck").forEach((row) => {
      if (row.querySelector(".jdp-play")) return;
      const due = [...row.querySelectorAll(
        ".new-count, .learn-count, .review-count")]
        .some((s) => parseInt(s.textContent, 10) > 0);
      const cell = row.querySelector("td.decktd");
      if (!due || !cell) return;
      const b = document.createElement("button");
      b.className = "jdp-play";
      b.title = "Study this deck";
      b.textContent = "Study";
      b.addEventListener("click", (e) => {
        e.stopPropagation();
        pycmd("jdp:study:" + row.id);
      });
      cell.appendChild(b);
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", decorate);
  } else {
    decorate();
  }
})();

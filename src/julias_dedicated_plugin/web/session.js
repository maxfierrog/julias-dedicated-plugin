/* Reviewer top row: [← Decks] [progress track] [time left], plus an optional
   break reminder. State is pushed from Python. */
(function () {
  "use strict";

  function root() {
    let r = document.getElementById("jdp-session");
    if (!r) {
      r = document.createElement("div");
      r.id = "jdp-session";
      r.innerHTML =
        '<div class="jdp-session-row">' +
        '<button type="button" class="jdp-exit" title="Back to decks (D)">← Decks</button>' +
        '<div class="jdp-track" role="progressbar" aria-valuemin="0" aria-valuemax="100">' +
        "<i></i><span></span></div>" +
        '<span class="jdp-time"></span></div>' +
        '<div class="jdp-fatigue" hidden><span class="jdp-cup">☕</span><span class="jdp-msg"></span>' +
        '<button type="button" aria-label="Dismiss">✕</button></div>';
      r.querySelector(".jdp-exit").addEventListener("click", () =>
        pycmd("jdp:decks"),
      );
      r.querySelector(".jdp-fatigue button").addEventListener("click", () =>
        pycmd("jdp:fatigue-dismiss"),
      );
      document.body.appendChild(r);
    }
    return r;
  }

  window.jdpSession = {
    update(s) {
      const r = root();
      const pct = Math.round(s.progress * 1000) / 10;
      const track = r.querySelector(".jdp-track");
      track.hidden = !s.show_progress;
      track.setAttribute("aria-valuenow", String(Math.round(pct)));
      track.querySelector("i").style.width = Math.max(pct, 2) + "%";
      track.querySelector("span").textContent = `${s.done} done · ${s.remaining} to go`;
      r.querySelector(".jdp-time").textContent =
        s.show_eta && s.eta ? `about ${s.eta} left` : "";
      const f = r.querySelector(".jdp-fatigue");
      f.hidden = !s.fatigue;
      f.querySelector(".jdp-msg").textContent =
        `${s.minutes} minutes in, and accuracy is dipping. ` +
        "A five-minute break usually helps more than pushing on.";
    },
  };

  // Show the exit right away, before the first state push.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", root);
  } else {
    root();
  }
})();

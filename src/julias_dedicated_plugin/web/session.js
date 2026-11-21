/* Review screen header, centered above the card:
     [← Decks] [=========== progress ===========]
               12 of 72 done · about 24 min left · done by 4:40
   plus an optional break reminder. State is pushed from Python. */
(function () {
  "use strict";

  function root() {
    let r = document.getElementById("jdp-session");
    if (!r) {
      r = document.createElement("div");
      r.id = "jdp-session";
      r.innerHTML =
        '<div class="jdp-session-inner">' +
        '<button type="button" class="jdp-exit" title="Back to decks (D)">← Decks</button>' +
        '<div class="jdp-progress">' +
        '<div class="jdp-track" role="progressbar" aria-valuemin="0" aria-valuemax="100"><i></i></div>' +
        '<div class="jdp-caption"></div></div></div>' +
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

  function b(text) {
    const e = document.createElement("b");
    e.textContent = text;
    return e;
  }

  window.jdpSession = {
    update(s) {
      const r = root();
      const pct = Math.round(s.progress * 1000) / 10;
      const track = r.querySelector(".jdp-track");
      track.setAttribute("aria-valuenow", String(Math.round(pct)));
      track.querySelector("i").style.width = Math.max(pct, 1.5) + "%";
      r.querySelector(".jdp-progress").hidden = !s.show_progress && !s.show_eta;
      track.hidden = !s.show_progress;

      const cap = r.querySelector(".jdp-caption");
      const parts = [];
      if (s.show_progress) {
        const total = s.done + s.remaining;
        parts.push([b(String(s.done)), ` of ${total} done`]);
      }
      if (s.show_eta && s.eta) {
        parts.push([b(s.eta)]);
        parts.push([`done by ${s.finish}`]);
      }
      cap.replaceChildren(
        ...parts.flatMap((p, i) => (i ? [" · ", ...p] : p)),
      );

      const f = r.querySelector(".jdp-fatigue");
      f.hidden = !s.fatigue;
      f.querySelector(".jdp-msg").textContent =
        `${s.minutes} minutes in, and accuracy is dipping. ` +
        "A five-minute break usually helps more than pushing on.";
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", root);
  } else {
    root();
  }
})();

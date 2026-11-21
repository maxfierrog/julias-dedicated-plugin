/* Session display in the reviewer. State is pushed from Python. */
(function () {
  "use strict";

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function root() {
    let r = document.getElementById("jdp-session");
    if (!r) {
      r = el("div");
      r.id = "jdp-session";
      r.innerHTML =
        '<div class="jdp-progress"><i></i></div>' +
        '<div class="jdp-session-row">' +
        '<span class="jdp-done"></span><span class="jdp-eta"></span></div>' +
        '<div class="jdp-fatigue" hidden><span></span>' +
        '<button type="button" aria-label="Dismiss">✕</button></div>';
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
      r.hidden = !(s.show_progress || s.show_eta);
      r.querySelector(".jdp-progress").hidden = !s.show_progress;
      r.querySelector(".jdp-progress i").style.width =
        Math.round(s.progress * 1000) / 10 + "%";
      r.querySelector(".jdp-done").textContent = s.show_progress
        ? `${s.done} done · ${s.remaining} left`
        : "";
      r.querySelector(".jdp-eta").textContent =
        s.show_eta && s.eta ? `about ${s.eta} · done ~${s.finish}` : "";
      const f = r.querySelector(".jdp-fatigue");
      f.hidden = !s.fatigue;
      f.querySelector("span").textContent =
        `${s.minutes} minutes in, and your accuracy has dipped. ` +
        "A five-minute break usually helps more than pushing on.";
    },
  };
})();

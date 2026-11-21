/* Customize window. Builds the UI from a declarative schema; every change is
   sent to Python immediately (pycmd "jdp:set:[path, value]"), which saves it
   and updates the main window live. */
(function () {
  "use strict";

  const ACCENTS = [
    ["#2F5DA8", "Ink"],
    ["#4C7A57", "Sage"],
    ["#6A55C9", "Violet"],
    ["#C0583A", "Terracotta"],
    ["#B4436C", "Raspberry"],
    ["#2E8585", "Teal"],
    ["#A67C1F", "Ochre"],
    ["#4A4A4A", "Graphite"],
  ];
  const CARD_FONTS = [
    ["atkinson", "Atkinson", '"Atkinson Hyperlegible"', "Built for legibility"],
    ["literata", "Literata", '"Literata Variable"', "Bookish serif"],
    ["nunito", "Nunito", '"Nunito Variable"', "Soft and round"],
    ["system", "System", "-apple-system, sans-serif", "Your Mac's font"],
  ];

  // Data is defined by an inline script after this file loads.
  let data;
  let s;

  const get = (path) => path.split(".").reduce((o, k) => o[k], s);
  function set(path, value) {
    if (path.startsWith("anki.")) {
      // Anki's own preference, not stored in our settings.
      if (path === "anki.mode") data.mode = value;
    } else {
      const keys = path.split(".");
      const last = keys.pop();
      keys.reduce((o, k) => o[k], s)[last] = value;
    }
    pycmd("jdp:set:" + JSON.stringify([path, value]));
    render();
  }

  function h(tag, attrs, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else if (k === "style" && typeof v === "object") Object.assign(e.style, v);
      else if (v === true) e.setAttribute(k, "");
      else if (v !== false && v != null) e.setAttribute(k, v);
    }
    for (const c of children.flat()) {
      if (c != null) e.append(c.nodeType ? c : document.createTextNode(c));
    }
    return e;
  }

  // ---- Controls ---------------------------------------------------------
  function row(label, hint, control, stack) {
    return h(
      "div",
      { class: "row" + (stack ? " stack" : "") },
      h("div", { class: "label" }, h("span", {}, label), hint && h("small", {}, hint)),
      control,
    );
  }

  function segmented(path, options, current) {
    const value = current !== undefined ? current : get(path);
    return h(
      "div",
      { class: "seg", role: "radiogroup" },
      options.map(([v, label]) =>
        h(
          "button",
          {
            type: "button",
            role: "radio",
            "aria-checked": String(v === value),
            class: v === value ? "on" : "",
            onclick: () => set(path, v),
          },
          label,
        ),
      ),
    );
  }

  function toggle(path) {
    const on = get(path);
    return h(
      "button",
      {
        type: "button",
        role: "switch",
        "aria-checked": String(on),
        class: "switch" + (on ? " on" : ""),
        onclick: () => set(path, !on),
      },
      h("i"),
    );
  }

  function slider(path, min, max, step, fmt) {
    const v = get(path);
    const out = h("output", {}, fmt(v));
    const input = h("input", {
      type: "range",
      min,
      max,
      step,
      value: v,
      oninput: (e) => (out.textContent = fmt(+e.target.value)),
      onchange: (e) => set(path, +e.target.value),
    });
    return h("div", { class: "slider" }, input, out);
  }

  // ---- Sections ---------------------------------------------------------
  function presets() {
    const cur = get("theme.preset");
    return h(
      "div",
      { class: "presets" },
      Object.entries(data.presets).map(([key, p]) =>
        h(
          "button",
          {
            type: "button",
            class: "preset" + (key === cur ? " on" : ""),
            "aria-pressed": String(key === cur),
            onclick: () => set("theme.preset", key),
          },
          h(
            "span",
            { class: "swatch" },
            h("i", { style: { background: p.light[0] } },
              h("b", { style: { background: p.light[1] } }),
              h("em", { style: { background: p.light[2] } })),
            h("i", { style: { background: p.dark[0] } },
              h("b", { style: { background: p.dark[1] } }),
              h("em", { style: { background: p.dark[2] } })),
          ),
          h("span", { class: "name" }, p.name),
        ),
      ),
    );
  }

  function accents() {
    const cur = get("theme.accent");
    const chips = ACCENTS.map(([hex, name]) =>
      h("button", {
        type: "button",
        class: "chip" + (cur.toLowerCase() === hex.toLowerCase() ? " on" : ""),
        title: name,
        "aria-label": name,
        style: `--c:${hex}`,
        onclick: () => set("theme.accent", hex),
      }),
    );
    const custom = h("input", {
      type: "color",
      title: "Pick any color",
      value: cur || "#2F5DA8",
      onchange: (e) => set("theme.accent", e.target.value.toUpperCase()),
    });
    return h(
      "div",
      { class: "chips" },
      h(
        "button",
        {
          type: "button",
          class: "chip auto" + (cur === "" ? " on" : ""),
          title: "Theme's own accent",
          onclick: () => set("theme.accent", ""),
        },
        "Auto",
      ),
      chips,
      h("label", { class: "chip custom", title: "Custom color" }, custom, "+"),
    );
  }

  function cardFonts() {
    const cur = get("cards.font");
    return h(
      "div",
      { class: "fonts" },
      CARD_FONTS.map(([key, name, family, hint]) =>
        h(
          "button",
          {
            type: "button",
            class: "font" + (key === cur ? " on" : ""),
            onclick: () => set("cards.font", key),
          },
          h("span", { class: "aa", style: { fontFamily: family } }, "Aa"),
          h("span", { class: "name" }, name),
          h("small", {}, hint),
        ),
      ),
    );
  }

  function nameField() {
    return h("input", {
      type: "text",
      class: "text",
      value: get("name"),
      placeholder: "Your name",
      maxlength: 40,
      onchange: (e) => set("name", e.target.value.trim()),
    });
  }

  function section(title, ...rows) {
    return h("section", {}, h("h2", {}, title), ...rows);
  }

  function render() {
    const app = document.getElementById("app");
    const scroll = document.scrollingElement.scrollTop;
    const radiusLabel = (v) => (v <= 4 ? "Crisp" : v <= 11 ? "Soft" : v <= 19 ? "Round" : "Bubbly");
    app.replaceChildren(
      h(
        "header",
        {},
        h("h1", {}, "Make it yours"),
        h("p", {}, "Changes show up right away, and follow you to every computer you sync."),
      ),
      section(
        "Look",
        presets(),
        row("Accent color", null, accents(), true),
        row("Appearance", "Auto follows your Mac", segmented("anki.mode", [[0, "Auto"], [1, "Light"], [2, "Dark"]], data.mode)),
        row("Corners", null, slider("theme.radius", 0, 28, 1, radiusLabel)),
        row("Spacing", null, segmented("theme.density", [["compact", "Compact"], ["comfortable", "Comfortable"]])),
        row("Font", "Used everywhere except card text",  segmented("theme.ui_font", [["rounded", "Rounded"], ["playful", "Playful"], ["inter", "Crisp"], ["system", "System"]])),
      ),
      section(
        "Cards",
        cardFonts(),
        row("Text size", null, slider("cards.size", 16, 32, 1, (v) => v + " px")),
        row("Line width", "Shorter lines are easier to read", segmented("cards.width", [["narrow", "Narrow"], ["medium", "Medium"], ["wide", "Wide"]])),
        row("Alignment", "Auto centers short cards and left-aligns long ones", segmented("cards.align", [["auto", "Auto"], ["center", "Center"], ["left", "Left"]])),
        row("Card style", null, segmented("cards.surface", [["sheet", "Sheet"], ["plain", "Plain"]])),
        row("Use theme colors on cards", "Replaces each deck's own background and text colors", toggle("cards.override_colors")),
        row("Images in dark mode", "Inverted works well for diagrams, not photos", segmented("cards.dark_images", [["none", "Original"], ["dim", "Dimmed"], ["invert", "Inverted"]])),
        row("Restyle cards", null, toggle("modules.cards")),
      ),
      section(
        "Studying",
        row("Focus mode", "Hides the top bar while you review", toggle("session.focus_mode")),
        row("Session bar", "Progress line and cards left", toggle("modules.session")),
        row("Time left", "Estimated from your own pace", toggle("session.show_eta")),
        row("Break reminders", "A gentle nudge when accuracy drops late in a long session", toggle("modules.fatigue")),
      ),
      section(
        "Home",
        row("Your name", null, nameField()),
        row("Greeting", null, toggle("briefing.greeting")),
        row("Briefing and widgets", "Greeting, summary and widgets on the home screen. Use “Edit widgets” at the bottom of it to choose and arrange them.", toggle("modules.briefing")),
      ),
      section(
        "Everything else",
        row("Restyle Anki", "Theme colors, fonts and layout on every screen", toggle("modules.theme")),
        h(
          "div",
          { class: "actions" },
          h("button", { type: "button", class: "primary", onclick: () => pycmd("jdp:feedback:") }, "Send feedback or an idea"),
          h("button", { type: "button", onclick: () => confirm("Reset every setting to its default?") && pycmd("jdp:reset:") }, "Reset to defaults"),
        ),
        h("p", { class: "version" }, `Julia's Dedicated Plugin ${data.version}`),
      ),
    );
    document.scrollingElement.scrollTop = scroll;
  }

  window.jdpSettings = {
    load(d) {
      data = d;
      s = d.settings;
      render();
    },
    sync(settings) {
      s = settings;
      render();
    },
  };
  function start() {
    data = window.JDP_DATA;
    s = data.settings;
    render();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

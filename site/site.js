// Toolbar for the reference site (not part of facet itself). Load it as a classic script in the
// <head>: it applies the saved theme, language and accent before first paint, then builds the
// toolbar once the page has parsed. Choices persist in localStorage["facet-site"] as
// {theme, lang, accent}; the theme toggle's own "facet-theme" value takes precedence over the
// theme saved here. URL parameters (?theme=light&lang=zh&accent=rose) override and are remembered.
// Bilingual text: any element with a data-zh attribute shows that (as HTML) in Chinese and its
// original content in English.
(function () {
  var KEY = "facet-site";
  var THEME_KEY = "facet-theme";
  var ROOT = document.documentElement;
  var BASE = document.currentScript ? document.currentScript.src.replace(/[^/]*$/, "") : "";

  var PAGES = [
    ["index.html", "Overview", "概览"],
    ["tokens.html", "Tokens", "令牌"],
    ["color.html", "Color", "色彩"],
    ["type.html", "Type", "字体"],
    ["components.html", "Components", "组件"],
    ["layouts/index.html", "Layouts", "版式"],
    ["cast.html", "Cast", "角色"],
  ];
  // name, label, hue; near-neutrals and graphite have their own chroma or fixed colors in site.css.
  var ACCENTS = [
    ["rose", "Rose", "玫瑰"],
    ["clay", "Clay", "陶土"],
    ["ochre", "Ochre", "赭黄"],
    ["moss", "Moss", "苔绿"],
    ["sage", "Sage", "鼠尾草"],
    ["teal", "Teal", "青"],
    ["slate", "Slate", "石板"],
    ["lavender", "Lavender", "薰衣草"],
    ["stone", "Stone", "石"],
    ["lichen", "Lichen", "地衣"],
    ["steel", "Steel", "钢"],
    ["heather", "Heather", "石南"],
    ["graphite", "Graphite", "石墨"],
  ];

  function get(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }
  function set(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {}
  }

  var THEMES = ["dark", "light", "auto"];
  var LANGS = ["en", "zh"];
  var ACCENT_NAMES = ACCENTS.map(function (a) {
    return a[0];
  });
  // A value outside the allowed set is ignored, so a bogus one is never applied or saved.
  function pick(value, allowed) {
    return allowed.indexOf(value) >= 0 ? value : null;
  }

  var saved = {};
  try {
    saved = JSON.parse(get(KEY) || "{}") || {};
  } catch (e) {}
  var state = {
    theme: pick(get(THEME_KEY), THEMES) || pick(saved.theme, THEMES) || "dark",
    lang: pick(saved.lang, LANGS) || "en",
    accent: pick(saved.accent, ACCENT_NAMES) || "",
  };
  var params = new URLSearchParams(location.search);
  var fromUrl = {
    theme: pick(params.get("theme"), THEMES),
    lang: pick(params.get("lang"), LANGS),
    accent: pick(params.get("accent"), ACCENT_NAMES),
  };
  var overridden = false;
  Object.keys(fromUrl).forEach(function (k) {
    if (fromUrl[k]) {
      state[k] = fromUrl[k];
      overridden = true;
    }
  });
  if (overridden) save();

  function save() {
    set(KEY, JSON.stringify(state));
    set(THEME_KEY, state.theme);
  }

  function applyRoot() {
    ROOT.dataset.theme = state.theme;
    ROOT.lang = state.lang === "zh" ? "zh-Hans" : "en";
    if (state.accent) ROOT.dataset.accent = state.accent;
  }
  applyRoot();

  function apply() {
    applyRoot();
    var nodes = document.querySelectorAll("[data-zh]");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.dataset.en === undefined) el.dataset.en = el.innerHTML;
      var html = state.lang === "zh" ? el.dataset.zh : el.dataset.en;
      if (el.innerHTML !== html) el.innerHTML = html;
    }
    var buttons = document.querySelectorAll(".site-bar button[data-k]");
    for (var j = 0; j < buttons.length; j++) {
      var b = buttons[j];
      b.setAttribute("aria-pressed", String(state[b.dataset.k] === b.dataset.v));
    }
    document.dispatchEvent(new CustomEvent("site:change", { detail: state }));
  }

  function segment(key, items) {
    return (
      '<span class="f-segmented" role="group" aria-label="' +
      key +
      '">' +
      items
        .map(function (it) {
          return (
            '<button type="button" data-k="' +
            key +
            '" data-v="' +
            it[0] +
            '">' +
            it[1] +
            "</button>"
          );
        })
        .join("") +
      "</span>"
    );
  }

  function build() {
    // The page's path relative to the site root, so "layouts/index.html" is not "index.html".
    var root = BASE ? new URL(BASE).pathname : "/";
    var here = location.pathname.indexOf(root) === 0 ? location.pathname.slice(root.length) : "";
    if (here === "" || here.slice(-1) === "/") here += "index.html";
    var bar = document.createElement("header");
    bar.className = "site-bar";
    var links = PAGES.map(function (p) {
      var current =
        here === p[0] || (p[0] === "layouts/index.html" && here.indexOf("layouts/") === 0);
      return (
        '<a href="' +
        BASE +
        p[0] +
        '"' +
        (current ? ' aria-current="page"' : "") +
        ' data-zh="' +
        p[2] +
        '">' +
        p[1] +
        "</a>"
      );
    }).join("");
    var dots = ACCENTS.map(function (a) {
      return (
        '<button type="button" class="site-dot" data-hue="' +
        a[0] +
        '" data-k="accent" data-v="' +
        a[0] +
        '" title="' +
        a[1] +
        '" aria-label="' +
        a[1] +
        '"></button>'
      );
    }).join("");
    bar.innerHTML =
      '<a class="site-bar__brand" href="' +
      BASE +
      'index.html">facet</a>' +
      '<nav class="site-bar__nav" aria-label="Reference site">' +
      links +
      "</nav>" +
      '<span class="site-bar__tools">' +
      segment("theme", [
        ["dark", "Dark"],
        ["light", "Light"],
        ["auto", "Auto"],
      ]) +
      segment("lang", [
        ["en", "EN"],
        ["zh", "中文"],
      ]) +
      '<span class="site-dots" role="group" aria-label="Accent">' +
      dots +
      "</span></span>";
    document.body.prepend(bar);
    bar.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-k]");
      if (!b) return;
      state[b.dataset.k] = b.dataset.v;
      save();
      apply();
    });
    // Fixed navs sit below the bar until it scrolls away.
    function offset() {
      ROOT.style.setProperty(
        "--site-bar-offset",
        Math.max(0, bar.offsetHeight - window.scrollY) + "px",
      );
    }
    addEventListener("scroll", offset, { passive: true });
    addEventListener("resize", offset);
    offset();
    if (window.ResizeObserver) new ResizeObserver(offset).observe(bar);
    apply();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();

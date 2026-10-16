// Toolbar for the mockup pages: page links, dark/light, English/Chinese and the
// accent. Choices persist in localStorage; URL parameters override
// them. Bilingual text: any element with a data-zh attribute shows that (as
// HTML) in Chinese, and its original content in English.

const PAGES = [
  ["index.html", "Mockups"],
  ["preview.html", "Preview"],
  ["type.html", "Type"],
  ["color.html", "Color"],
  ["shape.html", "Shape"],
  ["glass.html", "Glass"],
  ["layouts.html", "Layout"],
  ["cast.html", "Cast"],
];
const SITES = [
  ["moss", "Moss", "oklch(0.76 0.06 130)"],
  ["slate", "Slate", "oklch(0.76 0.06 255)"],
  ["sage", "Sage", "oklch(0.76 0.06 165)"],
  ["rose", "Rose", "oklch(0.76 0.06 15)"],
  ["graphite", "Graphite", "#9aa3b0"],
];

const store = {
  get: (k, d) => {
    try {
      return localStorage.getItem("facet-mk-" + k) ?? d;
    } catch {
      return d;
    }
  },
  set: (k, v) => {
    try {
      localStorage.setItem("facet-mk-" + k, v);
    } catch {}
  },
};

const root = document.documentElement;
const state = {
  theme: store.get("theme", "dark"),
  lang: store.get("lang", "en"),
  site: store.get("site", "moss"),
};
// ?theme=light&lang=zh&site=slate overrides (and remembers) the stored choices.
for (const [k, v] of new URLSearchParams(location.search)) {
  if (k in state) {
    state[k] = v;
    store.set(k, v);
  }
}

function apply() {
  root.dataset.theme = state.theme;
  root.dataset.site = state.site;
  root.lang = state.lang === "zh" ? "zh-Hans" : "en";
  for (const el of document.querySelectorAll("[data-zh]")) {
    if (el.dataset.en === undefined) el.dataset.en = el.innerHTML;
    el.innerHTML = state.lang === "zh" ? el.dataset.zh : el.dataset.en;
  }
  for (const b of document.querySelectorAll(".mk-bar .mk-seg button")) {
    b.setAttribute("aria-pressed", state[b.dataset.k] === b.dataset.v);
  }
  document.dispatchEvent(new CustomEvent("mk:change", { detail: state }));
}

function seg(k, items) {
  return `<span class="mk-seg">${items
    .map(([v, label, dot]) => {
      const d = dot ? `<span class="mk-dot" style="background:${dot}"></span>` : "";
      const l = dot ? `<span class="mk-lbl">${label}</span>` : label;
      return `<button type="button" data-k="${k}" data-v="${v}" title="${label}">${d}${l}</button>`;
    })
    .join("")}</span>`;
}

const here = location.pathname.split("/").pop() || "index.html";
const bar = document.createElement("header");
bar.className = "mk-bar";
bar.innerHTML =
  `<b>facet</b><nav>${PAGES.map(
    ([href, label]) =>
      `<a href="${href}"${href === here || (href === "layouts.html" && here.startsWith("layout-")) ? ' aria-current="page"' : ""}>${label}</a>`,
  ).join("")}</nav><span class="mk-sp"></span>` +
  seg("theme", [
    ["dark", "Dark"],
    ["light", "Light"],
  ]) +
  seg("lang", [
    ["en", "EN"],
    ["zh", "中文"],
  ]) +
  seg("site", SITES);
document.body.prepend(bar);
bar.addEventListener("click", (e) => {
  const b = e.target.closest("button[data-k]");
  if (!b) return;
  state[b.dataset.k] = b.dataset.v;
  store.set(b.dataset.k, b.dataset.v);
  apply();
});

apply();

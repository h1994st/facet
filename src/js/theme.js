// Theme toggle: dark → light → auto. Persists to localStorage; dark is the default.
const KEY = "facet-theme";
const ORDER = ["dark", "light", "auto"];
const LABEL = { dark: "Dark", light: "Light", auto: "Auto" };

export function setTheme(value) {
  document.documentElement.dataset.theme = value;
  try {
    localStorage.setItem(KEY, value);
  } catch {}
  for (const b of document.querySelectorAll("[data-f-theme-toggle]")) {
    b.textContent = LABEL[value];
    b.setAttribute("aria-label", `Theme: ${LABEL[value]}`);
  }
}

export function init(root = document) {
  let saved = "dark";
  try {
    saved = localStorage.getItem(KEY) || "dark";
  } catch {}
  if (!document.documentElement.dataset.theme) setTheme(saved);
  const handlers = [];
  for (const b of root.querySelectorAll("[data-f-theme-toggle]")) {
    const on = () => {
      const cur = document.documentElement.dataset.theme || "dark";
      setTheme(ORDER[(ORDER.indexOf(cur) + 1) % ORDER.length]);
    };
    b.addEventListener("click", on);
    handlers.push(() => b.removeEventListener("click", on));
    b.textContent = LABEL[document.documentElement.dataset.theme || "dark"];
  }
  return () => handlers.forEach((h) => h());
}

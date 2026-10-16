// facet's optional behavior. Import once: <script type="module" src=".../dist/js/facet.js">.
// Each module initializes the elements that opt in with a data-f-* attribute.
const modules = [];
modules.push(() => import("./theme.js"));
modules.push(() => import("./liquid.js"));

export async function init(root = document) {
  for (const load of modules) (await load()).init(root);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => init());
} else {
  init();
}

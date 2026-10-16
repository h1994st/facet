// facet's optional behavior. Import once: <script type="module" src=".../dist/js/facet.js">.
// Each module initializes the elements that opt in with a data-f-* attribute and returns a
// cleanup function. Imported statically, so the whole graph loads with the page and every module
// is running by the time the load event fires (a chain of dynamic imports finished later, so
// early input, such as a deck's arrow keys, was lost).
import * as theme from "./theme.js";
import * as liquid from "./liquid.js";
import * as scrollspy from "./scrollspy.js";
import * as nav from "./nav.js";
import * as autoplay from "./autoplay.js";
import * as story from "./story.js";
import * as panels from "./panels.js";
import * as deck from "./deck.js";

const modules = [theme, liquid, scrollspy, nav, autoplay, story, panels, deck];

export function init(root = document) {
  const cleanups = modules.map((m) => m.init(root));
  return () => cleanups.forEach((f) => typeof f === "function" && f());
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => init());
} else {
  init();
}

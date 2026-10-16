// Scroll spy: the link whose section top has passed 30% of the viewport is current.
export function init(root = document) {
  const off = [];
  for (const nav of root.querySelectorAll("[data-f-scrollspy]")) {
    const links = [...nav.querySelectorAll('a[href^="#"]')];
    const targets = links.map((a) => document.getElementById(a.hash.slice(1)));
    const update = () => {
      let cur = 0;
      targets.forEach((t, i) => {
        if (t && t.getBoundingClientRect().top < innerHeight * 0.3) cur = i;
      });
      links.forEach((a, i) =>
        i === cur ? a.setAttribute("aria-current", "location") : a.removeAttribute("aria-current"),
      );
    };
    addEventListener("scroll", update, { passive: true });
    update();
    off.push(() => removeEventListener("scroll", update));
  }
  return () => off.forEach((f) => f());
}

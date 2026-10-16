// Scroll spy: the link whose section top has passed 30% of the viewport is current.
const done = new WeakSet();

// a.hash is percent-encoded (#安装 reads as #%E5%AE%89%E8%A3%85); ids are not.
const idOf = (a) => {
  const raw = a.hash.slice(1);
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
};

export function init(root = document) {
  const off = [];
  for (const nav of root.querySelectorAll("[data-f-scrollspy]")) {
    if (done.has(nav)) continue;
    done.add(nav);
    const links = [...nav.querySelectorAll('a[href^="#"]')];
    const targets = links.map((a) => document.getElementById(idOf(a)));
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
    off.push(() => {
      removeEventListener("scroll", update);
      done.delete(nav);
    });
  }
  return () => off.forEach((f) => f());
}

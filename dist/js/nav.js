// Nav over a cover: <nav class="f-nav f-nav--over" data-f-nav-cover="#cover"> stays clear while
// the cover fills the screen and turns to glass (.is-scrolled) once less than 12% of it is visible.
// Tracked on scroll, so a fast scroll or a jump never leaves the nav in the wrong state.
export function init(root = document) {
  const off = [];
  for (const nav of root.querySelectorAll("[data-f-nav-cover]")) {
    const cover = document.querySelector(nav.dataset.fNavCover);
    if (!cover) continue;
    const update = () => {
      const r = cover.getBoundingClientRect();
      const seen = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
      nav.classList.toggle("is-scrolled", seen < r.height * 0.12);
    };
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
    update();
    off.push(() => {
      removeEventListener("scroll", update);
      removeEventListener("resize", update);
    });
  }
  return () => off.forEach((f) => f());
}

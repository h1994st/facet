// Full-page panels: <main class="f-panels" data-f-panels> of .f-panel sections, plus an optional
// empty <nav class="f-dots">. The panel filling most of the screen is current: it gets .is-on
// (its .f-reveal text arrives), its video plays and the others pause, its dot is lit, and a
// .f-nav--over stays clear over media panels and turns to glass over .f-panel--plain ones (the
// dots switch to page colors there too).
// Tracked on scroll, so a fast scroll never skips a panel.
export function init(root = document) {
  const off = [];
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  for (const host of root.querySelectorAll("[data-f-panels]")) {
    const panels = [...host.querySelectorAll(".f-panel")];
    if (!panels.length) continue;
    const nav = document.querySelector(".f-nav--over");
    const dots = document.querySelector("nav.f-dots");
    const buttons = [];
    if (dots) {
      panels.forEach((p, i) => {
        const b = document.createElement("button");
        b.type = "button";
        b.setAttribute("aria-label", p.querySelector("h2")?.textContent.trim() || `${i + 1}`);
        b.addEventListener("click", () =>
          p.scrollIntoView({ behavior: still ? "auto" : "smooth" }),
        );
        dots.append(b);
        buttons.push(b);
      });
    }
    host.classList.add("is-ready");
    let current = -1;
    const update = () => {
      let best = 0;
      let most = -1;
      panels.forEach((p, i) => {
        const r = p.getBoundingClientRect();
        const seen = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
        // Settled: the panel fills more than 55% of the screen.
        p.classList.toggle("is-on", seen > innerHeight * 0.55);
        if (seen > most) [best, most] = [i, seen];
      });
      if (best === current) return;
      current = best;
      panels.forEach((p, i) => {
        const v = p.querySelector("video");
        if (!v) return;
        if (i === best && !still) v.play().catch(() => {});
        else v.pause();
      });
      buttons.forEach((b, i) =>
        i === best ? b.setAttribute("aria-current", "step") : b.removeAttribute("aria-current"),
      );
      const plain = panels[best].classList.contains("f-panel--plain");
      nav?.classList.toggle("is-scrolled", plain);
      dots?.classList.toggle("is-over-plain", plain);
    };
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
    update();
    off.push(() => {
      removeEventListener("scroll", update);
      removeEventListener("resize", update);
      buttons.forEach((b) => b.remove());
      host.classList.remove("is-ready");
    });
  }
  return () => off.forEach((f) => f());
}

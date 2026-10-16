// Behavior shared by the layout mockups: the liquid hover on cards, the nav turning to glass once
// the page scrolls past a cover, a table of contents that tracks the section in view, and the
// cats on the footer line. Each page imports what it uses.
import { createCat } from "./cast/cast.js";

export function liquidCards(root = document) {
  for (const card of root.querySelectorAll(".card")) {
    card.addEventListener("pointerenter", (e) => {
      if (e.pointerType === "mouse") card.classList.add("hot");
    });
    card.addEventListener("pointerleave", () => card.classList.remove("hot"));
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--lx", e.clientX - r.left + "px");
      card.style.setProperty("--ly", e.clientY - r.top + "px");
    });
  }
}

// Marks the nav `.scrolled` once `cover` has mostly left the viewport.
export function navOverCover(nav, cover) {
  const io = new IntersectionObserver(
    ([e]) => nav.classList.toggle("scrolled", e.intersectionRatio < 0.12),
    { threshold: [0, 0.12, 0.5, 1] },
  );
  io.observe(cover);
}

// Highlights the TOC link of the section nearest the top of the viewport.
export function scrollSpy(links) {
  const targets = links.map((a) => document.querySelector(a.getAttribute("href")));
  const update = () => {
    let current = 0;
    targets.forEach((t, i) => {
      if (t && t.getBoundingClientRect().top < window.innerHeight * 0.3) current = i;
    });
    links.forEach((a, i) =>
      i === current
        ? a.setAttribute("aria-current", "location")
        : a.removeAttribute("aria-current"),
    );
  };
  addEventListener("scroll", update, { passive: true });
  update();
}

export function footerCats(footer) {
  footer.append(
    createCat("dudu", { label: "" }),
    createCat("nangnang", { label: "" }),
    createCat("duna", { pose: "wave", label: "" }),
  );
}

// A page-local segmented switch: <div class="pctl" data-k="..."><button data-v>…</div>.
export function pageSwitch(el, onChange) {
  const set = (v) => {
    for (const b of el.querySelectorAll("button"))
      b.setAttribute("aria-pressed", b.dataset.v === v);
    onChange(v);
  };
  el.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) set(b.dataset.v);
  });
  set(el.querySelector("button").dataset.v);
}

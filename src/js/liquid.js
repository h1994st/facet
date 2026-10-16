// Liquid hover: a light that follows the pointer on cards, mouse only.
export function init(root = document) {
  const off = [];
  for (const host of root.querySelectorAll("[data-f-liquid]")) {
    const cards = host.matches(".f-card") ? [host] : [...host.querySelectorAll(".f-card")];
    for (const card of cards) {
      const enter = (e) => e.pointerType === "mouse" && card.classList.add("is-hot");
      const leave = () => card.classList.remove("is-hot");
      const move = (e) => {
        const r = card.getBoundingClientRect();
        card.style.setProperty("--f-lx", `${e.clientX - r.left}px`);
        card.style.setProperty("--f-ly", `${e.clientY - r.top}px`);
      };
      card.addEventListener("pointerenter", enter);
      card.addEventListener("pointerleave", leave);
      card.addEventListener("pointermove", move);
      off.push(() => {
        card.removeEventListener("pointerenter", enter);
        card.removeEventListener("pointerleave", leave);
        card.removeEventListener("pointermove", move);
      });
    }
  }
  return () => off.forEach((f) => f());
}

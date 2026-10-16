// Variants: <div class="f-segmented" data-f-variants="look" hidden> with <button data-variant="x"
// aria-pressed> children switches every [data-f-variant="look:x"] element inside the control's
// parent. The control and the non-default variants ship hidden, so without JS the first variant
// shows and there are no dead buttons. The pressed button (else the first) picks the variant;
// elements of other groups are never touched. Cleanup hides the control again and restores the
// initial hidden state.
const done = new WeakSet();

export function init(root = document) {
  const off = [];
  for (const control of root.querySelectorAll("[data-f-variants]")) {
    if (done.has(control) || !control.parentElement) continue;
    const group = control.dataset.fVariants;
    const scope = control.parentElement;
    const buttons = [...control.querySelectorAll("button[data-variant]")];
    if (!group || !buttons.length) continue;
    done.add(control);
    const targets = [...scope.querySelectorAll("[data-f-variant]")].filter((el) =>
      el.dataset.fVariant.startsWith(`${group}:`),
    );
    const initial = targets.map((el) => [el, el.hidden]);
    const pressed = buttons.map((b) => b.getAttribute("aria-pressed"));
    const wasHidden = control.hidden;
    const select = (value) => {
      for (const b of buttons) b.setAttribute("aria-pressed", String(b.dataset.variant === value));
      for (const el of targets) el.hidden = el.dataset.fVariant !== `${group}:${value}`;
    };
    const chosen = buttons.find((b) => b.getAttribute("aria-pressed") === "true") || buttons[0];
    select(chosen.dataset.variant);
    control.hidden = false;
    const onClick = (e) => {
      const b = e.target.closest("button[data-variant]");
      if (b && control.contains(b)) select(b.dataset.variant);
    };
    control.addEventListener("click", onClick);
    off.push(() => {
      control.removeEventListener("click", onClick);
      control.hidden = wasHidden;
      for (const [el, h] of initial) el.hidden = h;
      buttons.forEach((b, i) =>
        pressed[i] === null
          ? b.removeAttribute("aria-pressed")
          : b.setAttribute("aria-pressed", pressed[i]),
      );
      done.delete(control);
    });
  }
  return () => off.forEach((f) => f());
}

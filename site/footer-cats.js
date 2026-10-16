import { createCat } from "./dist/cast/cast.js";

const slot = document.querySelector(".f-footer__cats");
if (slot)
  slot.append(
    createCat("dudu", { label: "" }),
    createCat("nangnang", { label: "" }),
    createCat("duna", { pose: "wave", label: "" }),
  );

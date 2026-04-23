def _build_formula_items(self, mfd_res, image, interline_enable=True):
        formula_list = []
        crop_targets = []

        for item in mfd_res or []:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            if label not in ["inline_formula", "display_formula"]:
                continue
            if not interline_enable and label == "display_formula":
                continue

            new_item = dict(item)
            new_item.setdefault("latex", "")
            formula_list.append(new_item)

            bbox = self._item_to_bbox(new_item, image)
            if bbox is not None:
                crop_targets.append((new_item, bbox))

        return formula_list, crop_targets
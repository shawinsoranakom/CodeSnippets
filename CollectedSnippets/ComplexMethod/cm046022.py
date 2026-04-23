def _extract_table_inline_objects(
        cls,
        layout_res: list[dict],
        np_img: np.ndarray,
        formula_enable: bool,
    ) -> dict[int, list[dict]]:
        image_h, image_w = np_img.shape[:2]
        image_size = (image_h, image_w)

        tables = []
        for res in layout_res:
            if res.get("label") != "table":
                continue
            table_bbox = normalize_to_int_bbox(res.get("bbox"), image_size=image_size)
            if table_bbox is None:
                continue
            tables.append((res, table_bbox))

        if not tables:
            return {}

        table_inline_objects = {id(table_res): [] for table_res, _ in tables}
        remove_ids = set()
        candidate_labels = {"image"}
        if formula_enable:
            candidate_labels.update({"inline_formula", "display_formula"})

        for layout_item in layout_res:
            label = layout_item.get("label")
            if label not in candidate_labels:
                continue

            item_bbox = normalize_to_int_bbox(layout_item.get("bbox"), image_size=image_size)
            if item_bbox is None:
                continue

            item_center = cls._bbox_center(item_bbox)
            matched_tables = []
            for table_res, table_bbox in tables:
                if not cls._is_point_in_bbox(item_center, table_bbox):
                    continue
                overlap_area = cls._bbox_intersection_area(item_bbox, table_bbox)
                matched_tables.append((overlap_area, table_res, table_bbox))

            if not matched_tables:
                continue

            matched_tables.sort(key=lambda item: item[0], reverse=True)
            _, table_res, table_bbox = matched_tables[0]
            overlap_bbox = cls._bbox_intersection(item_bbox, table_bbox)
            if overlap_bbox is None:
                continue

            rel_overlap_bbox = cls._bbox_to_relative_bbox(overlap_bbox, table_bbox)
            score = float(layout_item.get("score", 1.0))

            if label == "image":
                image_src = cls._encode_table_inline_image(np_img, item_bbox)
                if not image_src:
                    continue
                content = f'<img src="{image_src}"/>'
                token_bbox = cls._get_virtual_image_bbox(rel_overlap_bbox)
                kind = "image"
            else:
                latex = layout_item.get("latex", "")
                if not latex:
                    continue
                content = f"<eq>{html.escape(latex)}</eq>"
                token_bbox = rel_overlap_bbox
                kind = "formula"

            table_inline_objects[id(table_res)].append(
                {
                    "kind": kind,
                    "page_bbox": item_bbox,
                    "table_rel_mask_bbox": rel_overlap_bbox,
                    "table_token_bbox": token_bbox,
                    "content": content,
                    "score": score,
                }
            )
            remove_ids.add(id(layout_item))

        if remove_ids:
            layout_res[:] = [item for item in layout_res if id(item) not in remove_ids]

        return table_inline_objects
def _insert_patch_index_tokens(self, text: str, bboxes: list[tuple[int]] | list[tuple[float]]) -> str:
        if bboxes is None or len(bboxes) == 0:
            return text

        matched_phrases = list(re.finditer(r"<phrase>.+?</phrase>", string=text))
        if len(matched_phrases) != len(bboxes):
            raise ValueError(
                f"The number of elements in `bboxes` should be the same as the number of `<phrase> ... </phrase>` pairs in `text`. Got {len(matched_phrases)} v.s. {len(bboxes)} instead."
            )

        # insert object's patch index tokens
        # the found `<phrase> ... </phrase>` pairs.
        curr_pos = 0
        buffer = []
        for matched, bbox in zip(matched_phrases, bboxes):
            _, end = matched.span()
            buffer.append(text[curr_pos:end])
            curr_pos = end
            # A phrase without bbox
            if bbox is None:
                continue
            # A phrase with a single bbox
            if isinstance(bbox, tuple):
                bbox = [bbox]
            patch_index_strings = []
            # A phrase could have multiple bboxes
            if not all(box is not None for box in bbox):
                raise ValueError(
                    "The multiple bounding boxes for a single phrase should not contain any `None` value."
                )
            for box in bbox:
                patch_index_1, patch_index_2 = self._convert_bbox_to_patch_index_tokens(box)
                patch_index_strings.append(f"{patch_index_1} {patch_index_2}")
            # `bbox` being an empty list
            if len(patch_index_strings) == 0:
                continue
            position_str = " </delimiter_of_multi_objects/> ".join(patch_index_strings)
            buffer.append(f"<object> {position_str} </object>")
        # remaining
        if curr_pos < len(text):
            buffer.append(text[curr_pos:])

        text = "".join(buffer)
        return text
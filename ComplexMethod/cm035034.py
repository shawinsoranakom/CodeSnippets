def __call__(self, data):
        cells = data["cells"]
        structure = data["structure"]
        if self.merge_no_span_structure:
            structure = self._merge_no_span_structure(structure)
        if self.replace_empty_cell_token:
            structure = self._replace_empty_cell_token(structure, cells)
        # remove empty token and add " " to span token
        new_structure = []
        for token in structure:
            if token != "":
                if "span" in token and token[0] != " ":
                    token = " " + token
                new_structure.append(token)
        # encode structure
        structure = self.encode(new_structure)
        if structure is None:
            return None
        data["length"] = len(structure)
        structure = [self.start_idx] + structure + [self.end_idx]  # add sos abd eos
        structure = structure + [self.pad_idx] * (
            self._max_text_len - len(structure)
        )  # pad
        structure = np.array(structure)
        data["structure"] = structure

        if len(structure) > self._max_text_len:
            return None

        # encode box
        bboxes = np.zeros((self._max_text_len, self.loc_reg_num), dtype=np.float32)
        bbox_masks = np.zeros((self._max_text_len, 1), dtype=np.float32)

        bbox_idx = 0

        for i, token in enumerate(structure):
            if self.idx2char[token] in self.td_token:
                if "bbox" in cells[bbox_idx] and len(cells[bbox_idx]["tokens"]) > 0:
                    bbox = cells[bbox_idx]["bbox"].copy()
                    bbox = np.array(bbox, dtype=np.float32).reshape(-1)
                    bboxes[i] = bbox
                    bbox_masks[i] = 1.0
                if self.learn_empty_box:
                    bbox_masks[i] = 1.0
                bbox_idx += 1
        data["bboxes"] = bboxes
        data["bbox_masks"] = bbox_masks
        return data
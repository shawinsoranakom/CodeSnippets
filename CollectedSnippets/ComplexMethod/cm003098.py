def parse_description_with_bboxes_from_text_and_spans(
        self,
        text: str,
        image_size: tuple[int, int],
        allow_empty_phrase: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Parse descriptions with bounding boxes.

        Args:
            text (`str`):
                The generated text.
            image_size (`tuple[int, int]`):
                Image size (width, height).
            allow_empty_phrase (`bool`, *optional*, defaults to `False`):
                Allow phrases without text.

        Returns:
            `list[dict[str, Any]]`: list of instances with 'bbox', 'cat_name', and optional 'score'.
        """
        text = text.replace("<s>", "").replace("</s>", "").replace("<pad>", "")

        if allow_empty_phrase:
            pattern = r"(?:(?:<loc_\d+>){4,})"
        else:
            pattern = r"([^<]+(?:<loc_\d+>){4,})"
        phrases = re.findall(pattern, text)

        text_pattern = r"^\s*(.*?)(?=<od>|</od>|<box>|</box>|<bbox>|</bbox>|<loc_)"
        box_pattern = r"<loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)>"

        instances = []
        for phrase_text in phrases:
            phrase_text = phrase_text.replace("<ground>", "", 1).replace("<obj>", "", 1)
            if not phrase_text and not allow_empty_phrase:
                continue
            match = re.search(text_pattern, phrase_text)
            if not match:
                continue
            phrase = match.group().strip()
            boxes_matches = list(re.finditer(box_pattern, phrase_text))
            if not boxes_matches:
                continue
            bbox_bins = [[int(m.group(j)) for j in range(1, 5)] for m in boxes_matches]
            bboxes = self.dequantize(torch.tensor(bbox_bins), size=image_size).tolist()

            phrase = phrase.encode("ascii", "ignore").decode("ascii")
            for bbox in bboxes:
                instance = {"bbox": bbox, "cat_name": phrase}
                instances.append(instance)

        return instances
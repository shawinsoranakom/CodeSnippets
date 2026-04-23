def parse_phrase_grounding_from_text_and_spans(
        self, text: str, image_size: tuple[int, int]
    ) -> list[dict[str, Any]]:
        """
        Parse phrase grounding results.

        Args:
            text (`str`):
                The generated text.
            image_size (`tuple[int, int]`):
                Image size (width, height).

        Returns:
            `list[dict[str, Any]]`: list of instances with 'bbox' and 'cat_name'.
        """
        text = text.replace("<s>", "").replace("</s>", "").replace("<pad>", "")
        phrase_pattern = r"([^<]+(?:<loc_\d+>){4,})"
        phrases = re.findall(phrase_pattern, text)
        text_pattern = r"^\s*(.*?)(?=<od>|</od>|<box>|</box>|<bbox>|</bbox>|<loc_)"
        box_pattern = r"<loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)>"

        instances = []
        for phrase_text in phrases:
            phrase_text = phrase_text.replace("<ground>", "", 1).replace("<obj>", "", 1)
            if not phrase_text:
                continue
            match = re.search(text_pattern, phrase_text)
            if not match:
                continue
            phrase = match.group().strip()
            if phrase in self.banned_grounding_tokens:
                continue
            boxes_matches = list(re.finditer(box_pattern, phrase_text))
            if not boxes_matches:
                continue
            bbox_bins = [[int(m.group(j)) for j in range(1, 5)] for m in boxes_matches]
            bboxes = self.dequantize(torch.tensor(bbox_bins), size=image_size).tolist()
            phrase = phrase.encode("ascii", "ignore").decode("ascii")
            instances.append({"bbox": bboxes, "cat_name": phrase})
        return instances
def parse_description_with_polygons_from_text_and_spans(
        self,
        text: str,
        image_size: tuple[int, int],
        allow_empty_phrase: bool = False,
        polygon_sep_token: str = "<sep>",
        polygon_start_token: str = "<poly>",
        polygon_end_token: str = "</poly>",
        with_box_at_start: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Parse descriptions with polygons.

        Args:
            text (`str`):
                The generated text.
            image_size (`tuple[int, int]`):
                Image size (width, height).
            allow_empty_phrase (`bool`, *optional*, defaults to `False`):
                Allow phrases without text.
            polygon_sep_token (`str`, *optional*, defaults to "<sep>"):
                Token separating polygons.
            polygon_start_token (`str`, *optional*, defaults to "<poly>"):
                Start token for polygons.
            polygon_end_token (`str`, *optional*, defaults to "</poly>"):
                End token for polygons.
            with_box_at_start (`bool`, *optional*, defaults to `False`):
                Whether a bounding box is at the start of polygons.

        Returns:
            `list[dict[str, Any]]`: list of instances with 'polygons', 'cat_name', and optional 'bbox'.
        """
        text = text.replace("<s>", "").replace("</s>", "").replace("<pad>", "")

        if allow_empty_phrase:
            pattern = rf"(?:(?:<loc_\d+>|{re.escape(polygon_sep_token)}|{re.escape(polygon_start_token)}|{re.escape(polygon_end_token)}){{4,}})"
        else:
            pattern = rf"([^<]+(?:<loc_\d+>|{re.escape(polygon_sep_token)}|{re.escape(polygon_start_token)}|{re.escape(polygon_end_token)}){{4,}})"
        phrases = re.findall(pattern, text)
        phrase_pattern = r"^\s*(.*?)(?=<od>|</od>|<box>|</box>|<bbox>|</bbox>|<loc_|<poly>)"
        poly_instance_pattern = rf"{re.escape(polygon_start_token)}(.*?){re.escape(polygon_end_token)}"
        box_pattern = rf"((?:<loc_\d+>)+)(?:{re.escape(polygon_sep_token)}|$)"

        instances = []
        for phrase_text in phrases:
            phrase_text_strip = re.sub(r"^<loc_\d+>", "", phrase_text, count=1)
            if not phrase_text_strip and not allow_empty_phrase:
                continue
            match = re.search(phrase_pattern, phrase_text_strip)
            if not match:
                continue
            phrase = match.group().strip()

            if polygon_start_token in phrase_text and polygon_end_token in phrase_text:
                poly_instances = [m.group(1) for m in re.finditer(poly_instance_pattern, phrase_text)]
            else:
                poly_instances = [phrase_text]

            for poly_inst in poly_instances:
                poly_matches = list(re.finditer(box_pattern, poly_inst))
                if len(poly_matches) == 0:
                    continue
                bbox = []
                polygons = []
                for poly_match in poly_matches:
                    poly_str = poly_match.group(1)
                    poly_bins = [int(m.group(1)) for m in re.finditer(r"<loc_(\d+)>", poly_str)]
                    if with_box_at_start and not bbox:
                        if len(poly_bins) > 4:
                            bbox = poly_bins[:4]
                            poly_bins = poly_bins[4:]
                        else:
                            bbox = [0, 0, 0, 0]
                    if len(poly_bins) % 2 == 1:
                        poly_bins = poly_bins[:-1]
                    poly_coords = (
                        self.dequantize(torch.tensor(poly_bins).reshape(-1, 2), size=image_size).flatten().tolist()
                    )
                    polygons.append(poly_coords)

                instance = {"cat_name": phrase, "polygons": polygons}
                if bbox:
                    instance["bbox"] = self.dequantize(torch.tensor([bbox]), size=image_size)[0].tolist()
                instances.append(instance)
        return instances
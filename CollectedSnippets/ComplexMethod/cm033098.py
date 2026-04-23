def _extract_figures_info(self, figures_data):
        self.figures = []
        self.descriptions = []
        self.positions = []

        for item in figures_data:
            # position
            if len(item) == 2 and isinstance(item[0], tuple) and len(item[0]) == 2 and isinstance(item[1], list) and isinstance(item[1][0], tuple) and len(item[1][0]) == 5:
                img_desc = item[0]
                img = ensure_pil_image(img_desc[0])
                if img is None:
                    continue
                assert len(img_desc) == 2 and isinstance(img_desc[1], list), "Should be (figure, [description])"
                self.figures.append(img)
                self.descriptions.append(img_desc[1])
                self.positions.append(item[1])
            else:
                img = ensure_pil_image(item[0])
                if img is None:
                    continue
                assert len(item) == 2 and isinstance(item[1], list), f"Unexpected form of figure data: get {len(item)=}, {item=}"
                self.figures.append(img)
                self.descriptions.append(item[1])
def _expand_image_tokens(
        self,
        text: list[TextInput],
        grids: list[list[int]],
    ):
        processed_text = []
        grid_index = 0
        for sample in text:
            while "<image>" in sample:
                grid = grids[grid_index]
                row, col = grid[0], grid[1]
                placeholder = f"<IMG_START>{'<IMG_ATOM>' * self.image_seq_length}<IMG_GRID>"
                if row * col > 1:
                    for r in range(row):
                        for c in range(col):
                            placeholder += f"{'<IMG_ATOM>' * self.image_seq_length}"
                            if c < col - 1:
                                placeholder += "<IMG_COL>"
                        if r < row - 1:
                            placeholder += "<IMG_ROW>"
                placeholder += "<IMG_END>"

                sample = sample.replace("<image>", placeholder, 1)
                grid_index += 1
            processed_text.append(sample)
        return processed_text
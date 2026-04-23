def _collect_shape_blocks(
        self,
        shape_entry: _FlattenedShape,
        linear_shapes: list[_FlattenedShape],
        shape_index: int,
        slide_width: int,
        slide_height: int,
    ) -> list:
        shape = shape_entry.shape
        shape_blocks = []
        previous_page = self.cur_page
        previous_list_block_stack = self.list_block_stack
        self.cur_page = shape_blocks
        self.list_block_stack = []

        try:
            if shape.has_table:
                self._handle_tables(shape)

            if getattr(shape, "has_chart", False):
                self._handle_chart(shape)

            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                later_shapes = linear_shapes[shape_index + 1 :]
                if not self._should_skip_picture(
                    shape_entry,
                    later_shapes,
                    slide_width,
                    slide_height,
                ):
                    self._handle_pictures(shape)

            if not hasattr(shape, "text"):
                return shape_blocks
            if shape.text is None:
                return shape_blocks
            if len(shape.text.strip()) == 0:
                return shape_blocks
            if not shape.has_text_frame:
                logger.warning("Warning: shape has text but not text_frame")
                return shape_blocks

            self._handle_text_elements(shape)
            return shape_blocks
        finally:
            self.cur_page = previous_page
            self.list_block_stack = previous_list_block_stack
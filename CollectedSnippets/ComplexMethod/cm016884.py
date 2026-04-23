def execute(cls, input: io.Image.Type | io.Mask.Type, scale_method: io.Combo.Type, resize_type: ResizeTypedDict) -> io.NodeOutput:
        selected_type = resize_type["resize_type"]
        if selected_type == ResizeType.SCALE_BY:
            return io.NodeOutput(scale_by(input, resize_type["multiplier"], scale_method))
        elif selected_type == ResizeType.SCALE_DIMENSIONS:
            return io.NodeOutput(scale_dimensions(input, resize_type["width"], resize_type["height"], scale_method, resize_type["crop"]))
        elif selected_type == ResizeType.SCALE_LONGER_DIMENSION:
            return io.NodeOutput(scale_longer_dimension(input, resize_type["longer_size"], scale_method))
        elif selected_type == ResizeType.SCALE_SHORTER_DIMENSION:
            return io.NodeOutput(scale_shorter_dimension(input, resize_type["shorter_size"], scale_method))
        elif selected_type == ResizeType.SCALE_WIDTH:
            return io.NodeOutput(scale_dimensions(input, resize_type["width"], 0, scale_method))
        elif selected_type == ResizeType.SCALE_HEIGHT:
            return io.NodeOutput(scale_dimensions(input, 0, resize_type["height"], scale_method))
        elif selected_type == ResizeType.SCALE_TOTAL_PIXELS:
            return io.NodeOutput(scale_total_pixels(input, resize_type["megapixels"], scale_method))
        elif selected_type == ResizeType.MATCH_SIZE:
            return io.NodeOutput(scale_match_size(input, resize_type["match"], scale_method, resize_type["crop"]))
        elif selected_type == ResizeType.SCALE_TO_MULTIPLE:
            return io.NodeOutput(scale_to_multiple_cover(input, resize_type["multiple"], scale_method))
        raise ValueError(f"Unsupported resize type: {selected_type}")
def _resolve_text_prompts(self, text, input_boxes):
        """
        Resolve text prompts by setting defaults based on prompt types.
        """
        # If no text provided, infer default based on prompt type
        if text is None:
            return "visual" if input_boxes else None

        if not isinstance(text, (list, tuple)):
            return text

        # Validate list/tuple length matches both prompt types if provided
        text = list(text)  # Convert to list to allow modification

        if input_boxes and len(text) != len(input_boxes):
            raise ValueError(
                f"The number of text prompts must match the number of input boxes. "
                f"Got {len(text)} text prompts and {len(input_boxes)} input boxes."
            )

        # Fill in None values with defaults based on corresponding prompt
        for i, text_value in enumerate(text):
            if text_value is None and input_boxes and input_boxes[i] is not None:
                text[i] = "visual"

        return text
def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        text_pair: PreTokenizedInput | list[PreTokenizedInput] | None = None,
        boxes: list[list[int]] | list[list[list[int]]] | None = None,
        word_labels: list[int] | list[list[int]] | None = None,
        text_target: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        text_pair_target: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        **kwargs,
    ) -> BatchEncoding:
        if text is None and text_target is None:
            raise ValueError("You need to specify either `text` or `text_target`.")
        if text is not None:
            # The context manager will send the inputs as normal texts and not text_target, but we shouldn't change the
            # input mode in this case.
            if not self._in_target_context_manager and hasattr(self, "_switch_to_input_mode"):
                self._switch_to_input_mode()
            encodings = self.call_boxes(text=text, text_pair=text_pair, boxes=boxes, word_labels=word_labels, **kwargs)
        if text_target is not None:
            if hasattr(self, "_switch_to_target_mode"):
                self._switch_to_target_mode()
            target_encodings = self._encode_plus(
                text=text_target,
                text_pair=text_pair_target,
                **kwargs,
            )
        # Leave back tokenizer in input mode
        if hasattr(self, "_switch_to_input_mode"):
            self._switch_to_input_mode()

        if text_target is None:
            return encodings
        elif text is None:
            return target_encodings
        else:
            encodings["labels"] = target_encodings["input_ids"]
            return encodings
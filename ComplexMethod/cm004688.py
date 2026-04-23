def _encode_plus(self, text, text_pair=None, suffix=None, suffix_first=False, add_special_tokens=True, **kwargs):
        is_infilling = False

        if suffix is not None:
            text_pair = suffix
            is_infilling = True
        elif "suffix" in kwargs:
            text_pair = kwargs.pop("suffix")
            is_infilling = True

        if isinstance(text, str) and self.fill_token is not None and self.fill_token in text and text_pair is None:
            text, text_pair = text.split(self.fill_token)
            is_infilling = True

        if not is_infilling:
            return super()._encode_plus(text, text_pair=text_pair, add_special_tokens=add_special_tokens, **kwargs)

        if (
            text_pair is None
            or (isinstance(text_pair, str) and len(text_pair) < 1)
            or (isinstance(text_pair, list) and len(text_pair) == 0)
        ):
            return super()._encode_plus(text, text_pair=text_pair, add_special_tokens=add_special_tokens, **kwargs)

        if None in (self.prefix_id, self.middle_id, self.suffix_id):
            raise ValueError(
                "The input includes a `prefix` and a `suffix` used for the infilling task,"
                " the `prefix_id, middle_id, suffix_id` must all be initialized. Current"
                f" values : {self.prefix_id, self.middle_id, self.suffix_id}"
            )

        self.set_infilling_processor(False, suffix_first=suffix_first, add_special_tokens=add_special_tokens)
        kwargs.pop("text_pair", None)

        if isinstance(text, str):
            text = " " + text
        elif isinstance(text, list):
            text = [" " + t if isinstance(t, str) else t for t in text]

        result = super()._encode_plus(text, text_pair=text_pair, add_special_tokens=True, **kwargs)
        self.set_infilling_processor(True)
        return result
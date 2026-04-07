def _assert_raises_or_warns_cm(
        self, func, cm_attr, expected_exception, expected_message
    ):
        with func(expected_exception) as cm:
            yield cm
        self.assertIn(expected_message, str(getattr(cm, cm_attr)))
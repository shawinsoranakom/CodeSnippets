def check(self, **kwargs):
        return [
            *self._check_string_if_invalid_is_string(),
            *self._check_for_template_tags_with_the_same_name(),
        ]
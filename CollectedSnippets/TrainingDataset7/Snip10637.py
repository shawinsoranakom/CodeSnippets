def _get_FIELD_display(self, field):
        value = getattr(self, field.attname)
        choices_dict = dict(make_hashable(field.flatchoices))
        # force_str() to coerce lazy strings.
        return force_str(
            choices_dict.get(make_hashable(value), value), strings_only=True
        )
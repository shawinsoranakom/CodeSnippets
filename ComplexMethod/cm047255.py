def _str_to_selection(self, model, field, value, savepoint):
        # get untranslated values
        env = self.with_context(lang=None).env
        selection = field.get_description(env)['selection']

        for item, label in selection:
            if callable(field.selection):
                labels = [label]
                for item2, label2 in field._description_selection(self.env):
                    if item2 == item:
                        labels.append(label2)
                        break
            else:
                labels = [label] + self._get_selection_translations(field, label)
            # case insensitive comparaison of string to allow to set the value even if the given 'value' param is not
            # exactly (case sensitive) the same as one of the selection item.
            if value.lower() == str(item).lower() or any(value.lower() == label.lower() for label in labels):
                return item, []

        if field.name in self.env.context.get('import_skip_records', []):
            return None, []
        elif field.name in self.env.context.get('import_set_empty_fields', []):
            return False, []
        raise self._format_import_error(
            ValueError,
            self.env._("Value '%s' not found in selection field '%%(field)s'"),
            value,
            {'moreinfo': [_label or str(item) for item, _label in selection if _label or item]}
        )
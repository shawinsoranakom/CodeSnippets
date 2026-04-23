def _perform_onchange(self, field_name=None):
        assert field_name is None or isinstance(field_name, str)

        # marks onchange source as changed
        if field_name:
            field_names = [field_name]
            self._values._changed.add(field_name)
        else:
            field_names = []

        # skip calling onchange() if there's no on_change on the field
        if field_name and not self._view['onchange'][field_name]:
            return

        record = self._record

        # if the onchange is triggered by a field, add the context of that field
        if field_name:
            context = self._get_context(field_name)
            if context:
                record = record.with_context(**context)

        values = self._get_onchange_values()
        result = record.onchange(values, field_names, self._view['fields_spec'])
        self._env.flush_all()
        self._env.clear()  # discard cache and pending recomputations

        if w := result.get('warning'):
            if isinstance(w, collections.abc.Mapping) and w.keys() >= {'title', 'message'}:
                _logger.getChild('onchange').warning("%(title)s %(message)s", w)
            else:
                _logger.getChild('onchange').error(
                    "received invalid warning %r from onchange on %r (should be a dict with keys `title` and `message`)",
                    w,
                    field_names,
                )

        if not field_name:
            # fill in whatever fields are still missing with falsy values
            self._values.update({
                field_name: _cleanup_from_default(field_info['type'], False)
                for field_name, field_info in self._view['fields'].items()
                if field_name not in self._values
            })

        if result.get('value'):
            self._apply_onchange(result['value'])

        return result
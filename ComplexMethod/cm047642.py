def __getitem__(self, property_name):
        """Will make the verification."""
        if not self.record:
            return False

        values = self.field.convert_to_read(
            self._values,
            self.record,
            use_display_name=False,
        )
        prop = next((p for p in values if p['name'] == property_name), False)
        if not prop:
            raise KeyError(property_name)

        if prop.get('type') == 'many2one' and prop.get('comodel'):
            return self.record.env[prop.get('comodel')].browse(prop.get('value'))

        if prop.get('type') == 'many2many' and prop.get('comodel'):
            return self.record.env[prop.get('comodel')].browse(prop.get('value'))

        if prop.get('type') == 'selection' and prop.get('value'):
            if self.record.env.context.get('property_selection_get_key'):
                return next((sel[0] for sel in prop.get('selection') if sel[0] == prop['value']), False)
            return next((sel[1] for sel in prop.get('selection') if sel[0] == prop['value']), False)

        if prop.get('type') == 'tags' and prop.get('value'):
            return ', '.join(tag[1] for tag in prop.get('tags') if tag[0] in prop['value'])

        return prop.get('value') or False
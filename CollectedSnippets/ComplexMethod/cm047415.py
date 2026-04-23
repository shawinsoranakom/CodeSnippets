def _res_users_settings_format(self, fields_to_format=None):
        self.ensure_one()
        fields_blacklist = self._get_fields_blacklist()
        if fields_to_format:
            fields_to_format = [field for field in fields_to_format if field not in fields_blacklist]
        else:
            fields_to_format = [name for name, field in self._fields.items() if name == 'id' or (name not in models.MAGIC_COLUMNS and name not in fields_blacklist)]
        res = self._format_settings(fields_to_format)
        return res
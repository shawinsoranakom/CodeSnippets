def evaluate_params(self, params, sort_extractor):
        self._use_free_order = params.get('prefer_free_formats', False)
        self._sort_user = params.get('format_sort', [])
        self._sort_extractor = sort_extractor

        def add_item(field, reverse, closest, limit_text):
            field = field.lower()
            if field in self._order:
                return
            self._order.append(field)
            limit = self._resolve_field_value(field, limit_text)
            data = {
                'reverse': reverse,
                'closest': False if limit is None else closest,
                'limit_text': limit_text,
                'limit': limit}
            if field in self.settings:
                self.settings[field].update(data)
            else:
                self.settings[field] = data

        sort_list = (
            tuple(field for field in self.default if self._get_field_setting(field, 'forced'))
            + (tuple() if params.get('format_sort_force', False)
                else tuple(field for field in self.default if self._get_field_setting(field, 'priority')))
            + tuple(self._sort_user) + tuple(sort_extractor) + self.default)

        for item in sort_list:
            match = re.match(self.regex, item)
            if match is None:
                raise ExtractorError(f'Invalid format sort string "{item}" given by extractor')
            field = match.group('field')
            if field is None:
                continue
            if self._get_field_setting(field, 'type') == 'alias':
                alias, field = field, self._get_field_setting(field, 'field')
                if self._get_field_setting(alias, 'deprecated'):
                    self.ydl.deprecated_feature(f'Format sorting alias {alias} is deprecated and may '
                                                f'be removed in a future version. Please use {field} instead')
            reverse = match.group('reverse') is not None
            closest = match.group('separator') == '~'
            limit_text = match.group('limit')

            has_limit = limit_text is not None
            has_multiple_fields = self._get_field_setting(field, 'type') == 'combined'
            has_multiple_limits = has_limit and has_multiple_fields and not self._get_field_setting(field, 'same_limit')

            fields = self._get_field_setting(field, 'field') if has_multiple_fields else (field,)
            limits = limit_text.split(':') if has_multiple_limits else (limit_text,) if has_limit else tuple()
            limit_count = len(limits)
            for (i, f) in enumerate(fields):
                add_item(f, reverse, closest,
                         limits[i] if i < limit_count
                         else limits[0] if has_limit and not has_multiple_limits
                         else None)
def _get_field_setting(self, field, key):
        if field not in self.settings:
            if key in ('forced', 'priority'):
                return False
            self.ydl.deprecated_feature(f'Using arbitrary fields ({field}) for format sorting is '
                                        'deprecated and may be removed in a future version')
            self.settings[field] = {}
        prop_obj = self.settings[field]
        if key not in prop_obj:
            type_ = prop_obj.get('type')
            if key == 'field':
                default = 'preference' if type_ == 'extractor' else (field,) if type_ in ('combined', 'multiple') else field
            elif key == 'convert':
                default = 'order' if type_ == 'ordered' else 'float_string' if field else 'ignore'
            else:
                default = {'type': 'field', 'visible': True, 'order': [], 'not_in_list': (None,)}.get(key)
            prop_obj[key] = default
        return prop_obj[key]
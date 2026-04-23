def print_verbose_info(self, write_debug):
        if self._sort_user:
            write_debug('Sort order given by user: {}'.format(', '.join(self._sort_user)))
        if self._sort_extractor:
            write_debug('Sort order given by extractor: {}'.format(', '.join(self._sort_extractor)))
        write_debug('Formats sorted by: {}'.format(', '.join(['{}{}{}'.format(
            '+' if self._get_field_setting(field, 'reverse') else '', field,
            '{}{}({})'.format('~' if self._get_field_setting(field, 'closest') else ':',
                              self._get_field_setting(field, 'limit_text'),
                              self._get_field_setting(field, 'limit'))
            if self._get_field_setting(field, 'limit_text') is not None else '')
            for field in self._order if self._get_field_setting(field, 'visible')])))
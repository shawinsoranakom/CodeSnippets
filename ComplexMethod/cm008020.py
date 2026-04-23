def _fill_common_fields(self, info_dict, final=True):
        # TODO: move sanitization here
        if final:
            title = info_dict['fulltitle'] = info_dict.get('title')
            if not title:
                if title == '':
                    self.write_debug('Extractor gave empty title. Creating a generic title')
                else:
                    self.report_warning('Extractor failed to obtain "title". Creating a generic title instead')
                info_dict['title'] = f'{info_dict["extractor"].replace(":", "-")} video #{info_dict["id"]}'

        if info_dict.get('duration') is not None:
            info_dict['duration_string'] = formatSeconds(info_dict['duration'])

        for ts_key, date_key in (
                ('timestamp', 'upload_date'),
                ('release_timestamp', 'release_date'),
                ('modified_timestamp', 'modified_date'),
        ):
            if info_dict.get(date_key) is None and info_dict.get(ts_key) is not None:
                info_dict[date_key] = strftime_or_none(info_dict[ts_key])

        if not info_dict.get('release_year'):
            info_dict['release_year'] = traverse_obj(info_dict, ('release_date', {lambda x: int(x[:4])}))

        live_keys = ('is_live', 'was_live')
        live_status = info_dict.get('live_status')
        if live_status is None:
            for key in live_keys:
                if info_dict.get(key) is False:
                    continue
                if info_dict.get(key):
                    live_status = key
                break
            if all(info_dict.get(key) is False for key in live_keys):
                live_status = 'not_live'
        if live_status:
            info_dict['live_status'] = live_status
            for key in live_keys:
                if info_dict.get(key) is None:
                    info_dict[key] = (live_status == key)
        if live_status == 'post_live':
            info_dict['was_live'] = True

        # Auto generate title fields corresponding to the *_number fields when missing
        # in order to always have clean titles. This is very common for TV series.
        for field in ('chapter', 'season', 'episode'):
            if final and info_dict.get(f'{field}_number') is not None and not info_dict.get(field):
                info_dict[field] = '%s %d' % (field.capitalize(), info_dict[f'{field}_number'])

        for old_key, new_key in self._deprecated_multivalue_fields.items():
            if new_key in info_dict and old_key in info_dict:
                if '_version' not in info_dict:  # HACK: Do not warn when using --load-info-json
                    self.deprecation_warning(f'Do not return {old_key!r} when {new_key!r} is present')
            elif old_value := info_dict.get(old_key):
                info_dict[new_key] = old_value.split(', ')
            elif new_value := info_dict.get(new_key):
                info_dict[old_key] = ', '.join(v.replace(',', '\N{FULLWIDTH COMMA}') for v in new_value)
def _fill_common_fields(self, info_dict, final=True):

        for ts_key, date_key in (
                ('timestamp', 'upload_date'),
                ('release_timestamp', 'release_date'),
        ):
            if info_dict.get(date_key) is None and info_dict.get(ts_key) is not None:
                # Working around out-of-range timestamp values (e.g. negative ones on Windows,
                # see http://bugs.python.org/issue1646728)
                try:
                    upload_date = datetime.datetime.utcfromtimestamp(info_dict[ts_key])
                    info_dict[date_key] = compat_str(upload_date.strftime('%Y%m%d'))
                except (ValueError, OverflowError, OSError):
                    pass

        # Auto generate title fields corresponding to the *_number fields when missing
        # in order to always have clean titles. This is very common for TV series.
        if final:
            for field in ('chapter', 'season', 'episode'):
                if info_dict.get('%s_number' % field) is not None and not info_dict.get(field):
                    info_dict[field] = '%s %d' % (field.capitalize(), info_dict['%s_number' % field])
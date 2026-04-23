def compute_value(self, records):
        bin_size_name = 'bin_size_' + self.name
        if records.env.context.get('bin_size') or records.env.context.get(bin_size_name):
            # always compute without bin_size
            records_no_bin_size = records.with_context(**{'bin_size': False, bin_size_name: False})
            super().compute_value(records_no_bin_size)
            # manually update the bin_size cache
            field_cache_data = self._get_cache(records_no_bin_size.env)
            field_cache_size = self._get_cache(records.env)
            for record in records:
                try:
                    value = field_cache_data[record.id]
                    # don't decode non-attachments to be consistent with pg_size_pretty
                    if not (self.store and self.column_type):
                        with contextlib.suppress(TypeError, binascii.Error):
                            value = base64.b64decode(value)
                    try:
                        if isinstance(value, (bytes, _BINARY)):
                            value = human_size(len(value))
                    except (TypeError):
                        pass
                    cache_value = self.convert_to_cache(value, record)
                    # the dirty flag is independent from this assignment
                    field_cache_size[record.id] = cache_value
                except KeyError:
                    pass
        else:
            super().compute_value(records)
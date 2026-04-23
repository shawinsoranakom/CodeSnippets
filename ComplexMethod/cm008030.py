def render_formats_table(self, info_dict):
        formats = self._get_formats(info_dict)
        if not formats:
            return
        if not self.params.get('listformats_table', True) is not False:
            table = [
                [
                    format_field(f, 'format_id'),
                    format_field(f, 'ext'),
                    self.format_resolution(f),
                    self._format_note(f),
                ] for f in formats if (f.get('preference') or 0) >= -1000]
            return render_table(['format code', 'extension', 'resolution', 'note'], table, extra_gap=1)

        def simplified_codec(f, field):
            assert field in ('acodec', 'vcodec')
            codec = f.get(field)
            if not codec:
                return 'unknown'
            elif codec != 'none':
                return '.'.join(codec.split('.')[:4])

            if field == 'vcodec' and f.get('acodec') == 'none':
                return 'images'
            elif field == 'acodec' and f.get('vcodec') == 'none':
                return ''
            return self._format_out('audio only' if field == 'vcodec' else 'video only',
                                    self.Styles.SUPPRESS)

        delim = self._format_out('\u2502', self.Styles.DELIM, '|', test_encoding=True)
        table = [
            [
                self._format_out(format_field(f, 'format_id'), self.Styles.ID),
                format_field(f, 'ext'),
                format_field(f, func=self.format_resolution, ignore=('audio only', 'images')),
                format_field(f, 'fps', '\t%d', func=round),
                format_field(f, 'dynamic_range', '%s', ignore=(None, 'SDR')).replace('HDR', ''),
                format_field(f, 'audio_channels', '\t%s'),
                delim, (
                    format_field(f, 'filesize', ' \t%s', func=format_bytes)
                    or format_field(f, 'filesize_approx', '≈\t%s', func=format_bytes)
                    or format_field(filesize_from_tbr(f.get('tbr'), info_dict.get('duration')), None,
                                    self._format_out('~\t%s', self.Styles.SUPPRESS), func=format_bytes)),
                format_field(f, 'tbr', '\t%dk', func=round),
                shorten_protocol_name(f.get('protocol', '')),
                delim,
                simplified_codec(f, 'vcodec'),
                format_field(f, 'vbr', '\t%dk', func=round),
                simplified_codec(f, 'acodec'),
                format_field(f, 'abr', '\t%dk', func=round),
                format_field(f, 'asr', '\t%s', func=format_decimal_suffix),
                join_nonempty(format_field(f, 'language', '[%s]'), join_nonempty(
                    self._format_out('UNSUPPORTED', self.Styles.BAD_FORMAT) if f.get('ext') in ('f4f', 'f4m') else None,
                    (self._format_out('Maybe DRM', self.Styles.WARNING) if f.get('has_drm') == 'maybe'
                     else self._format_out('DRM', self.Styles.BAD_FORMAT) if f.get('has_drm') else None),
                    self._format_out('Untested', self.Styles.WARNING) if f.get('__needs_testing') else None,
                    format_field(f, 'format_note'),
                    format_field(f, 'container', ignore=(None, f.get('ext'))),
                    delim=', '), delim=' '),
            ] for f in formats if f.get('preference') is None or f['preference'] >= -1000]
        header_line = self._list_format_headers(
            'ID', 'EXT', 'RESOLUTION', '\tFPS', 'HDR', 'CH', delim, '\tFILESIZE', '\tTBR', 'PROTO',
            delim, 'VCODEC', '\tVBR', 'ACODEC', '\tABR', '\tASR', 'MORE INFO')

        return render_table(
            header_line, table, hide_empty=True,
            delim=self._format_out('\u2500', self.Styles.DELIM, '-', test_encoding=True))
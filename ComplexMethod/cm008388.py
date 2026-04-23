def _merge_mpd_periods(self, periods):
        """
        Combine all formats and subtitles from an MPD manifest into a single list,
        by concatenate streams with similar formats.
        """
        formats, subtitles = {}, {}
        for period in periods:
            for f in period['formats']:
                assert 'is_dash_periods' not in f, 'format already processed'
                f['is_dash_periods'] = True
                format_key = tuple(v for k, v in f.items() if k not in (
                    ('format_id', 'fragments', 'manifest_stream_number')))
                if format_key not in formats:
                    formats[format_key] = f
                elif 'fragments' in f:
                    formats[format_key].setdefault('fragments', []).extend(f['fragments'])

            if subtitles and period['subtitles']:
                self.report_warning(bug_reports_message(
                    'Found subtitles in multiple periods in the DASH manifest; '
                    'if part of the subtitles are missing,',
                ), only_once=True)

            for sub_lang, sub_info in period['subtitles'].items():
                subtitles.setdefault(sub_lang, []).extend(sub_info)

        return list(formats.values()), subtitles
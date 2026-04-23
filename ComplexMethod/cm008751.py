def run(self, info):
        subs = info.get('requested_subtitles')
        new_ext = self.format
        new_format = new_ext
        if new_format == 'vtt':
            new_format = 'webvtt'
        if subs is None:
            self.to_screen('There aren\'t any subtitles to convert')
            return [], info
        self.to_screen('Converting subtitles')
        sub_filenames = []
        for lang, sub in subs.items():
            if not os.path.exists(sub.get('filepath', '')):
                self.report_warning(f'Skipping embedding {lang} subtitle because the file is missing')
                continue
            ext = sub['ext']
            if ext == new_ext:
                self.to_screen(f'Subtitle file for {new_ext} is already in the requested format')
                continue
            elif ext == 'json':
                self.to_screen(
                    'You have requested to convert json subtitles into another format, '
                    'which is currently not possible')
                continue
            old_file = sub['filepath']
            sub_filenames.append(old_file)
            new_file = replace_extension(old_file, new_ext)

            if ext in ('dfxp', 'ttml', 'tt'):
                self.report_warning(
                    'You have requested to convert dfxp (TTML) subtitles into another format, '
                    'which results in style information loss')

                dfxp_file = old_file
                srt_file = replace_extension(old_file, 'srt')

                with open(dfxp_file, 'rb') as f:
                    srt_data = dfxp2srt(f.read())

                with open(srt_file, 'w', encoding='utf-8') as f:
                    f.write(srt_data)
                old_file = srt_file

                subs[lang] = {
                    'ext': 'srt',
                    'data': srt_data,
                    'filepath': srt_file,
                }

                if new_ext == 'srt':
                    continue
                else:
                    sub_filenames.append(srt_file)

            self.run_ffmpeg(old_file, new_file, ['-f', new_format])

            with open(new_file, encoding='utf-8') as f:
                subs[lang] = {
                    'ext': new_ext,
                    'data': f.read(),
                    'filepath': new_file,
                }

            info['__files_to_move'][new_file] = replace_extension(
                info['__files_to_move'][sub['filepath']], new_ext)

        return sub_filenames, info
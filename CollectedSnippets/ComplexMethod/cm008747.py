def run(self, info):
        if info['ext'] not in self.SUPPORTED_EXTS:
            self.to_screen(f'Subtitles can only be embedded in {", ".join(self.SUPPORTED_EXTS)} files')
            return [], info
        subtitles = info.get('requested_subtitles')
        if not subtitles:
            self.to_screen('There aren\'t any subtitles to embed')
            return [], info

        filename = info['filepath']

        # Disabled temporarily. There needs to be a way to override this
        # in case of duration actually mismatching in extractor
        # See: https://github.com/yt-dlp/yt-dlp/issues/1870, https://github.com/yt-dlp/yt-dlp/issues/1385
        '''
        if info.get('duration') and not info.get('__real_download') and self._duration_mismatch(
                self._get_real_video_duration(filename, False), info['duration']):
            self.to_screen(f'Skipping {self.pp_key()} since the real and expected durations mismatch')
            return [], info
        '''

        ext = info['ext']
        sub_langs, sub_names, sub_filenames = [], [], []
        webm_vtt_warn = False
        mp4_ass_warn = False

        for lang, sub_info in subtitles.items():
            if not os.path.exists(sub_info.get('filepath', '')):
                self.report_warning(f'Skipping embedding {lang} subtitle because the file is missing')
                continue
            sub_ext = sub_info['ext']
            if sub_ext == 'json':
                self.report_warning('JSON subtitles cannot be embedded')
            elif ext != 'webm' or (ext == 'webm' and sub_ext == 'vtt'):
                sub_langs.append(lang)
                sub_names.append(sub_info.get('name'))
                sub_filenames.append(sub_info['filepath'])
            else:
                if not webm_vtt_warn and ext == 'webm' and sub_ext != 'vtt':
                    webm_vtt_warn = True
                    self.report_warning('Only WebVTT subtitles can be embedded in webm files')
            if not mp4_ass_warn and ext == 'mp4' and sub_ext == 'ass':
                mp4_ass_warn = True
                self.report_warning('ASS subtitles cannot be properly embedded in mp4 files; expect issues')

        if not sub_langs:
            return [], info

        input_files = [filename, *sub_filenames]

        opts = [
            *self.stream_copy_opts(ext=info['ext']),
            # Don't copy the existing subtitles, we may be running the
            # postprocessor a second time
            '-map', '-0:s',
        ]
        for i, (lang, name) in enumerate(zip(sub_langs, sub_names, strict=True)):
            opts.extend(['-map', f'{i + 1}:0'])
            lang_code = ISO639Utils.short2long(lang) or lang
            opts.extend([f'-metadata:s:s:{i}', f'language={lang_code}'])
            if name:
                opts.extend([f'-metadata:s:s:{i}', f'handler_name={name}',
                             f'-metadata:s:s:{i}', f'title={name}'])

        temp_filename = prepend_extension(filename, 'temp')
        self.to_screen(f'Embedding subtitles in "{filename}"')
        self.run_ffmpeg_multiple_files(input_files, temp_filename, opts)
        os.replace(temp_filename, filename)

        files_to_delete = [] if self._already_have_subtitle else sub_filenames
        return files_to_delete, info
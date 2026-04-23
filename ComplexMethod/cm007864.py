def run(self, information):
        if information['ext'] not in ('mp4', 'webm', 'mkv'):
            self._downloader.to_screen('[ffmpeg] Subtitles can only be embedded in mp4, webm or mkv files')
            return [], information
        subtitles = information.get('requested_subtitles')
        if not subtitles:
            self._downloader.to_screen('[ffmpeg] There aren\'t any subtitles to embed')
            return [], information

        filename = information['filepath']

        ext = information['ext']
        sub_langs = []
        sub_filenames = []
        webm_vtt_warn = False

        for lang, sub_info in subtitles.items():
            sub_ext = sub_info['ext']
            if ext != 'webm' or ext == 'webm' and sub_ext == 'vtt':
                sub_langs.append(lang)
                sub_filenames.append(subtitles_filename(filename, lang, sub_ext, ext))
            else:
                if not webm_vtt_warn and ext == 'webm' and sub_ext != 'vtt':
                    webm_vtt_warn = True
                    self._downloader.to_screen('[ffmpeg] Only WebVTT subtitles can be embedded in webm files')

        if not sub_langs:
            return [], information

        input_files = [filename] + sub_filenames

        opts = [
            '-map', '0',
            '-c', 'copy',
            # Don't copy the existing subtitles, we may be running the
            # postprocessor a second time
            '-map', '-0:s',
            # Don't copy Apple TV chapters track, bin_data (see #19042, #19024,
            # https://trac.ffmpeg.org/ticket/6016)
            '-map', '-0:d',
        ]
        if information['ext'] == 'mp4':
            opts += ['-c:s', 'mov_text']
        for (i, lang) in enumerate(sub_langs):
            opts.extend(['-map', '%d:0' % (i + 1)])
            lang_code = ISO639Utils.short2long(lang) or lang
            opts.extend(['-metadata:s:s:%d' % i, 'language=%s' % lang_code])

        temp_filename = prepend_extension(filename, 'temp')
        self._downloader.to_screen('[ffmpeg] Embedding subtitles in \'%s\'' % filename)
        self.run_ffmpeg_multiple_files(input_files, temp_filename, opts)
        os.remove(encodeFilename(filename))
        os.rename(encodeFilename(temp_filename), encodeFilename(filename))

        return sub_filenames, information
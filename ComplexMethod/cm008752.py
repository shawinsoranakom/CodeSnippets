def run(self, info):
        self._fixup_chapters(info)
        chapters = info.get('chapters') or []
        if not chapters:
            self.to_screen('Chapter information is unavailable')
            return [], info

        in_file = info['filepath']
        if self._force_keyframes and len(chapters) > 1:
            in_file = self.force_keyframes(in_file, (c['start_time'] for c in chapters))
        self.to_screen(f'Splitting video by chapters; {len(chapters)} chapters found')
        for idx, chapter in enumerate(chapters):
            destination, opts = self._ffmpeg_args_for_chapter(idx + 1, chapter, info)
            self.real_run_ffmpeg([(in_file, opts)], [(destination, self.stream_copy_opts())])
        if in_file != info['filepath']:
            self._delete_downloaded_files(in_file, msg=None)
        return [], info
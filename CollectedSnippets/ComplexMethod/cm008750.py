def _get_infojson_opts(self, info, infofn):
        if not infofn or not os.path.exists(infofn):
            if self._add_infojson is not True:
                return
            infofn = infofn or '%s.temp' % (
                self._downloader.prepare_filename(info, 'infojson')
                or replace_extension(self._downloader.prepare_filename(info), 'info.json', info['ext']))
            if not self._downloader._ensure_dir_exists(infofn):
                return
            self.write_debug(f'Writing info-json to: {infofn}')
            write_json_file(self._downloader.sanitize_info(info, self.get_param('clean_infojson', True)), infofn)
            info['infojson_filename'] = infofn

        old_stream, new_stream = self.get_stream_number(info['filepath'], ('tags', 'mimetype'), 'application/json')
        if old_stream is not None:
            yield ('-map', f'-0:{old_stream}')
            new_stream -= 1

        yield (
            '-attach', self._ffmpeg_filename_argument(infofn),
            f'-metadata:s:{new_stream}', 'mimetype=application/json',
            f'-metadata:s:{new_stream}', 'filename=info.json',
        )
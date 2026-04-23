def save(self):
        if self.stopped:
            return
        self.browser._websocket_send('Page.stopScreencast')
        # Wait for frames just in case, ideally we'd wait for the Browse.close
        # event or something but that doesn't exist.
        time.sleep(5)
        self.stopped = True
        if not self.frames:
            self._logger.debug('No screencast frames to encode')
            return

        frames, self.frames = self.frames, []
        t = time.time()
        duration = 1/24
        concat_script_path = self.frames_dir.with_suffix('.txt')
        with concat_script_path.open("w") as concat_file:
            for f, next_frame in zip_longest(frames, islice(frames, 1, None)):
                frame_file_path = f['file_path']

                if f['timestamp'] is not None:
                    end_time = next_frame['timestamp'] if next_frame else t
                    duration = end_time - f['timestamp']
                concat_file.write(f"file '{frame_file_path}'\nduration {duration}\n")
            concat_file.write(f"file '{frame_file_path}'")  # needed by the concat plugin

        try:
            ffmpeg_path = find_in_path('ffmpeg')
        except IOError:
            self._logger.runbot('Screencast frames in: %s', self.frames_dir)
            return

        outfile = self.frames_dir.with_suffix('.mp4')
        try:
            subprocess.run([
                ffmpeg_path,
                '-y', '-loglevel', 'warning',
                '-f', 'concat', '-safe', '0', '-i', concat_script_path,
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
                '-c:v', 'libx265', '-x265-params', 'lossless=1',
                outfile,
            ], preexec_fn=_preexec, check=True)
        except subprocess.CalledProcessError:
            self._logger.error('Failed to encode screencast, screencast frames in %s', self.frames_dir)
        else:
            concat_script_path.unlink()
            shutil.rmtree(self.frames_dir, ignore_errors=True)
            self._logger.runbot('Screencast in: %s', outfile)
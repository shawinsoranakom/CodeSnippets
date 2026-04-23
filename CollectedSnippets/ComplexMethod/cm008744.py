def get_audio_codec(self, path):
        if not self.probe_available and not self.available:
            raise PostProcessingError('ffprobe and ffmpeg not found. Please install or provide the path using --ffmpeg-location')
        try:
            if self.probe_available:
                cmd = [
                    self.probe_executable,
                    encodeArgument('-show_streams')]
            else:
                cmd = [
                    self.executable,
                    encodeArgument('-i')]
            cmd.append(self._ffmpeg_filename_argument(path))
            self.write_debug(f'{self.basename} command line: {shell_quote(cmd)}')
            stdout, stderr, returncode = Popen.run(
                cmd, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if returncode != (0 if self.probe_available else 1):
                return None
        except OSError:
            return None
        output = stdout if self.probe_available else stderr
        if self.probe_available:
            audio_codec = None
            for line in output.split('\n'):
                if line.startswith('codec_name='):
                    audio_codec = line.split('=')[1].strip()
                elif line.strip() == 'codec_type=audio' and audio_codec is not None:
                    return audio_codec
        else:
            # Stream #FILE_INDEX:STREAM_INDEX[STREAM_ID](LANGUAGE): CODEC_TYPE: CODEC_NAME
            mobj = re.search(
                r'Stream\s*#\d+:\d+(?:\[0x[0-9a-f]+\])?(?:\([a-z]{3}\))?:\s*Audio:\s*([0-9a-z]+)',
                output)
            if mobj:
                return mobj.group(1)
        return None
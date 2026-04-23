def run(self, information):
        orig_path = path = information['filepath']
        target_format, _skip_msg = resolve_mapping(information['ext'], self.mapping)
        if target_format == 'best' and information['ext'] in self.COMMON_AUDIO_EXTS:
            target_format, _skip_msg = None, 'the file is already in a common audio format'
        if not target_format:
            self.to_screen(f'Not converting audio {orig_path}; {_skip_msg}')
            return [], information

        filecodec = self.get_audio_codec(path)
        if filecodec is None:
            raise PostProcessingError('WARNING: unable to obtain file audio codec with ffprobe')

        if filecodec == 'aac' and target_format in ('m4a', 'best'):
            # Lossless, but in another container
            extension, _, more_opts, acodec = *ACODECS['m4a'], 'copy'
        elif target_format == 'best' or target_format == filecodec:
            # Lossless if possible
            try:
                extension, _, more_opts, acodec = *ACODECS[filecodec], 'copy'
            except KeyError:
                extension, acodec, more_opts = ACODECS['mp3']
        else:
            # We convert the audio (lossy if codec is lossy)
            extension, acodec, more_opts = ACODECS[target_format]
            if acodec == 'aac' and self._features.get('fdk'):
                acodec, more_opts = 'libfdk_aac', []

        more_opts = list(more_opts)
        if acodec != 'copy':
            more_opts = self._quality_args(acodec)

        temp_path = new_path = replace_extension(path, extension, information['ext'])

        if new_path == path:
            if acodec == 'copy':
                self.to_screen(f'Not converting audio {orig_path}; file is already in target format {target_format}')
                return [], information
            orig_path = prepend_extension(path, 'orig')
            temp_path = prepend_extension(path, 'temp')
        if (self._nopostoverwrites and os.path.exists(new_path)
                and os.path.exists(orig_path)):
            self.to_screen(f'Post-process file {new_path} exists, skipping')
            return [], information

        self.to_screen(f'Destination: {new_path}')
        self.run_ffmpeg(path, temp_path, acodec, more_opts)

        os.replace(path, orig_path)
        os.replace(temp_path, new_path)
        information['filepath'] = new_path
        information['ext'] = extension

        # Try to update the date time for extracted audio file.
        if information.get('filetime') is not None:
            self.try_utime(
                new_path, time.time(), information['filetime'], errnote='Cannot update utime of audio file')

        return [orig_path], information
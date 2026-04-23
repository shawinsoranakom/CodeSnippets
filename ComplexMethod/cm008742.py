def _determine_executables(self):
        programs = ['ffmpeg', 'ffprobe']

        location = self.get_param('ffmpeg_location', self._ffmpeg_location.get())
        if location is None:
            return {p: p for p in programs}

        if not os.path.exists(location):
            self.report_warning(
                f'ffmpeg-location {location} does not exist! Continuing without ffmpeg', only_once=True)
            return {}
        elif os.path.isdir(location):
            dirname, basename, filename = location, None, None
        else:
            filename = os.path.basename(location)
            basename = next((p for p in programs if p in filename), 'ffmpeg')
            dirname = os.path.dirname(os.path.abspath(location))

        paths = {p: os.path.join(dirname, p) for p in programs}
        if basename and basename in filename:
            for p in programs:
                path = os.path.join(dirname, filename.replace(basename, p))
                if os.path.exists(path):
                    paths[p] = path
        if basename:
            paths[basename] = location
        return paths
def _determine_executables(self):
        # ordered to match prefer_ffmpeg!
        convs = ['ffmpeg', 'avconv']
        probes = ['ffprobe', 'avprobe']
        prefer_ffmpeg = True
        programs = convs + probes

        def get_ffmpeg_version(path):
            ver = get_exe_version(path, args=['-version'])
            if ver:
                regexs = [
                    r'(?:\d+:)?([0-9.]+)-[0-9]+ubuntu[0-9.]+$',  # Ubuntu, see [1]
                    r'n([0-9.]+)$',  # Arch Linux
                    # 1. http://www.ducea.com/2006/06/17/ubuntu-package-version-naming-explanation/
                ]
                for regex in regexs:
                    mobj = re.match(regex, ver)
                    if mobj:
                        ver = mobj.group(1)
            return ver

        self.basename = None
        self.probe_basename = None

        self._paths = None
        self._versions = None
        location = None
        if self._downloader:
            prefer_ffmpeg = self._downloader.params.get('prefer_ffmpeg', True)
            location = self._downloader.params.get('ffmpeg_location')
            if location is not None:
                if not os.path.exists(location):
                    self._downloader.report_warning(
                        'ffmpeg-location %s does not exist! '
                        'Continuing without avconv/ffmpeg.' % (location))
                    self._versions = {}
                    return
                elif not os.path.isdir(location):
                    basename = os.path.splitext(os.path.basename(location))[0]
                    if basename not in programs:
                        self._downloader.report_warning(
                            'Cannot identify executable %s, its basename should be one of %s. '
                            'Continuing without avconv/ffmpeg.' %
                            (location, ', '.join(programs)))
                        self._versions = {}
                        return None
                    location = os.path.dirname(os.path.abspath(location))
                    if basename in ('ffmpeg', 'ffprobe'):
                        prefer_ffmpeg = True
        self._paths = dict(
            (p, p if location is None else os.path.join(location, p))
            for p in programs)
        self._versions = dict(
            x for x in (
                (p, get_ffmpeg_version(self._paths[p])) for p in programs)
            if x[1] is not None)

        basenames = [None, None]
        for i, progs in enumerate((convs, probes)):
            for p in progs[::-1 if prefer_ffmpeg is False else 1]:
                if self._versions.get(p):
                    basenames[i] = p
                    break
        self.basename, self.probe_basename = basenames
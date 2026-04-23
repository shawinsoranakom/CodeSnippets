def _get_ffmpeg_version(self, prog):
        path = self._paths.get(prog)
        if path in self._version_cache:
            return self._version_cache[path], self._features_cache.get(path, {})
        out = _get_exe_version_output(path, ['-bsfs'])
        ver = detect_exe_version(out) if out else False
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
        self._version_cache[path] = ver
        if prog != 'ffmpeg' or not out:
            return ver, {}

        mobj = re.search(r'(?m)^\s+libavformat\s+(?:[0-9. ]+)\s+/\s+(?P<runtime>[0-9. ]+)', out)
        lavf_runtime_version = mobj.group('runtime').replace(' ', '') if mobj else None
        self._features_cache[path] = features = {
            'fdk': '--enable-libfdk-aac' in out,
            'setts': 'setts' in out.splitlines(),
            'needs_adtstoasc': is_outdated_version(lavf_runtime_version, '57.56.100', False),
        }
        return ver, features
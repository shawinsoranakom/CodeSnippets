def _process_update_spec(self, lockfile: str, resolved_tag: str):
        lines = lockfile.splitlines()
        is_version2 = any(line.startswith('lockV2 ') for line in lines)

        for line in lines:
            if is_version2:
                if not line.startswith(f'lockV2 {self.requested_repo} '):
                    continue
                _, _, tag, pattern = line.split(' ', 3)
            else:
                if not line.startswith('lock '):
                    continue
                _, tag, pattern = line.split(' ', 2)

            if re.match(pattern, self._identifier):
                if _VERSION_RE.fullmatch(tag):
                    if not self._exact:
                        return tag
                    elif self._version_compare(tag, resolved_tag):
                        return resolved_tag
                elif tag != resolved_tag:
                    continue

                self._report_error(
                    f'yt-dlp cannot be updated to {resolved_tag} since you are on an older Python version '
                    'or your operating system is not compatible with the requested build', True)
                return None

        return resolved_tag
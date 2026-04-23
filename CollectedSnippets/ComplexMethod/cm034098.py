def _distro_release_info(self) -> Dict[str, str]:
        """
        Get the information items from the specified distro release file.

        Returns:
            A dictionary containing all information items.
        """
        if self.distro_release_file:
            # If it was specified, we use it and parse what we can, even if
            # its file name or content does not match the expected pattern.
            distro_info = self._parse_distro_release_file(self.distro_release_file)
            basename = os.path.basename(self.distro_release_file)
            # The file name pattern for user-specified distro release files
            # is somewhat more tolerant (compared to when searching for the
            # file), because we want to use what was specified as best as
            # possible.
            match = _DISTRO_RELEASE_BASENAME_PATTERN.match(basename)
        else:
            try:
                basenames = [
                    basename
                    for basename in os.listdir(self.etc_dir)
                    if basename not in _DISTRO_RELEASE_IGNORE_BASENAMES
                    and os.path.isfile(os.path.join(self.etc_dir, basename))
                ]
                # We sort for repeatability in cases where there are multiple
                # distro specific files; e.g. CentOS, Oracle, Enterprise all
                # containing `redhat-release` on top of their own.
                basenames.sort()
            except OSError:
                # This may occur when /etc is not readable but we can't be
                # sure about the *-release files. Check common entries of
                # /etc for information. If they turn out to not be there the
                # error is handled in `_parse_distro_release_file()`.
                basenames = _DISTRO_RELEASE_BASENAMES
            for basename in basenames:
                match = _DISTRO_RELEASE_BASENAME_PATTERN.match(basename)
                if match is None:
                    continue
                filepath = os.path.join(self.etc_dir, basename)
                distro_info = self._parse_distro_release_file(filepath)
                # The name is always present if the pattern matches.
                if "name" not in distro_info:
                    continue
                self.distro_release_file = filepath
                break
            else:  # the loop didn't "break": no candidate.
                return {}

        if match is not None:
            distro_info["id"] = match.group(1)

        # CloudLinux < 7: manually enrich info with proper id.
        if "cloudlinux" in distro_info.get("name", "").lower():
            distro_info["id"] = "cloudlinux"

        return distro_info
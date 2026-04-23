def version(self, pretty: bool = False, best: bool = False) -> str:
        """
        Return the version of the OS distribution, as a string.

        For details, see :func:`distro.version`.
        """
        versions = [
            self.os_release_attr("version_id"),
            self.lsb_release_attr("release"),
            self.distro_release_attr("version_id"),
            self._parse_distro_release_content(self.os_release_attr("pretty_name")).get(
                "version_id", ""
            ),
            self._parse_distro_release_content(
                self.lsb_release_attr("description")
            ).get("version_id", ""),
            self.uname_attr("release"),
        ]
        if self.uname_attr("id").startswith("aix"):
            # On AIX platforms, prefer oslevel command output.
            versions.insert(0, self.oslevel_info())
        elif self.id() == "debian" or "debian" in self.like().split():
            # On Debian-like, add debian_version file content to candidates list.
            versions.append(self._debian_version)
        version = ""
        if best:
            # This algorithm uses the last version in priority order that has
            # the best precision. If the versions are not in conflict, that
            # does not matter; otherwise, using the last one instead of the
            # first one might be considered a surprise.
            for v in versions:
                if v.count(".") > version.count(".") or version == "":
                    version = v
        else:
            for v in versions:
                if v != "":
                    version = v
                    break
        if pretty and version and self.codename():
            version = f"{version} ({self.codename()})"
        return version
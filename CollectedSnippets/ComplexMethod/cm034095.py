def name(self, pretty: bool = False) -> str:
        """
        Return the name of the OS distribution, as a string.

        For details, see :func:`distro.name`.
        """
        name = (
            self.os_release_attr("name")
            or self.lsb_release_attr("distributor_id")
            or self.distro_release_attr("name")
            or self.uname_attr("name")
        )
        if pretty:
            name = self.os_release_attr("pretty_name") or self.lsb_release_attr(
                "description"
            )
            if not name:
                name = self.distro_release_attr("name") or self.uname_attr("name")
                version = self.version(pretty=True)
                if version:
                    name = f"{name} {version}"
        return name or ""
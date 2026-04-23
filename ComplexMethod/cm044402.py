def parse_requirements(self, packages: list[str]) -> list[Requirement]:
        """ Drop in replacement for deprecated pkg_resources.parse_requirements

        Parameters
        ----------
        packages: list[str]
            List of packages formatted from a requirements.txt file

        Returns
        -------
        list[:class:`packaging.Requirement`]
            List of Requirement objects
        """
        self._import_packaging()
        assert self._requirement is not None
        requirements = [self._requirement(p) for p in packages]
        retval = [r for r in requirements if r.marker is None or r.marker.evaluate()]
        if len(retval) != len(requirements):
            logger.debug("Filtered invalid packages %s",
                         [(r.name, r.marker) for r in set(requirements).difference(set(retval))])
        logger.debug("Parsed requirements %s: %s", packages, retval)
        return retval
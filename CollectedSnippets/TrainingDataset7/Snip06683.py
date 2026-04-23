def proj_version_tuple(self):
        """
        Return the version of PROJ used by PostGIS as a tuple of the
        major, minor, and subminor release numbers.
        """
        proj_regex = re.compile(r"(\d+)\.(\d+)\.(\d+)")
        proj_ver_str = self.postgis_proj_version()
        m = proj_regex.search(proj_ver_str)
        if m:
            return tuple(map(int, m.groups()))
        else:
            raise Exception("Could not determine PROJ version from PostGIS.")
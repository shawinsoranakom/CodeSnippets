def parse(self, vstring):
        match = SEMVER_RE.match(vstring)
        if not match:
            raise ValueError("invalid semantic version '%s'" % vstring)

        (major, minor, patch, prerelease, buildmetadata) = match.group(1, 2, 3, 4, 5)
        self.vstring = vstring
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)

        if prerelease:
            self.prerelease = tuple(_Numeric(x) if x.isdigit() else _Alpha(x) for x in prerelease.split('.'))
        if buildmetadata:
            self.buildmetadata = tuple(_Numeric(x) if x.isdigit() else _Alpha(x) for x in buildmetadata.split('.'))
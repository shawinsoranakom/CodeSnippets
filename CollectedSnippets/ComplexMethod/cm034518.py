def _cmp(self, other):
        if isinstance(other, str):
            other = SemanticVersion(other)

        if self.core != other.core:
            # if the core version doesn't match
            # prerelease and buildmetadata doesn't matter
            if self.core < other.core:
                return -1
            else:
                return 1

        if not any((self.prerelease, other.prerelease)):
            return 0

        if self.prerelease and not other.prerelease:
            return -1
        elif not self.prerelease and other.prerelease:
            return 1
        else:
            if self.prerelease < other.prerelease:
                return -1
            elif self.prerelease > other.prerelease:
                return 1

        # Build metadata MUST be ignored when determining version precedence
        # https://semver.org/#spec-item-10
        # With the above in mind it is ignored here

        # If we have made it here, things should be equal
        return 0
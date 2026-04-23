def _cmp(self, other):
        if isinstance(other, str):
            other = StrictVersion(other)
        elif not isinstance(other, StrictVersion):
            return NotImplemented

        if self.version != other.version:
            # numeric versions don't match
            # prerelease stuff doesn't matter
            if self.version < other.version:
                return -1
            else:
                return 1

        # have to compare prerelease
        # case 1: neither has prerelease; they're equal
        # case 2: self has prerelease, other doesn't; other is greater
        # case 3: self doesn't have prerelease, other does: self is greater
        # case 4: both have prerelease: must compare them!

        if (not self.prerelease and not other.prerelease):
            return 0
        elif (self.prerelease and not other.prerelease):
            return -1
        elif (not self.prerelease and other.prerelease):
            return 1
        elif (self.prerelease and other.prerelease):
            if self.prerelease == other.prerelease:
                return 0
            elif self.prerelease < other.prerelease:
                return -1
            else:
                return 1
        else:
            raise AssertionError("never get here")
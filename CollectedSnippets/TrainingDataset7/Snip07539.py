def check_fid_range(self, fid_range):
        "Check the `fid_range` keyword."
        if fid_range:
            if isinstance(fid_range, (tuple, list)):
                return slice(*fid_range)
            elif isinstance(fid_range, slice):
                return fid_range
            else:
                raise TypeError
        else:
            return None
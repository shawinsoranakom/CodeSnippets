def specificity(self):
        """
        Return a value from 0-3 for how specific the media type is.
        """
        if self.main_type == "*":
            return 0
        elif self.sub_type == "*":
            return 1
        elif not self.range_params:
            return 2
        return 3
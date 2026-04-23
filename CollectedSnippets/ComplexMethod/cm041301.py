def ensure_sampled_exists(self, sampled=None):
        """
        Ensures that the sampled flag is set.
        Return self to allow for chaining.
        """
        if sampled is None:
            self._sampled = 1
        else:
            if sampled == "?":
                self._sampled = sampled
            if sampled is True or sampled == "1" or sampled == 1:
                self._sampled = 1
            if sampled is False or sampled == "0" or sampled == 0:
                self._sampled = 0
        return self
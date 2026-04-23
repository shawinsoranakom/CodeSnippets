def sanity_check(self):
        """
        Returns True if options comprise a valid sequence expression
        Raises AnsibleError if options are an invalid expression
        Returns false if options are valid but result in an empty sequence - these cases do not raise exceptions
        in order to maintain historic behavior
        """
        if self.count is None and self.end is None:
            raise AnsibleError("must specify count or end in with_sequence")
        elif self.count is not None and self.end is not None:
            raise AnsibleError("can't specify both count and end in with_sequence")
        elif self.count is not None:
            # convert count to end
            if self.count != 0:
                self.end = self.start + self.count * self.stride - 1
            else:
                return False
        if self.stride > 0 and self.end < self.start:
            raise AnsibleError("to count backwards make stride negative")
        if self.stride < 0 and self.end > self.start:
            raise AnsibleError("to count forward don't make stride negative")
        if self.stride == 0:
            return False
        if self.format.count('%') != 1:
            raise AnsibleError("bad formatting string: %s" % self.format)

        return True
def _find_boundary(self, data):
        """
        Find a multipart boundary in data.

        Should no boundary exist in the data, return None. Otherwise, return
        a tuple containing the indices of the following:
         * the end of current encapsulation
         * the start of the next encapsulation
        """
        index = data.find(self._boundary)
        if index < 0:
            return None
        else:
            end = index
            next = index + len(self._boundary)
            # backup over CRLF
            last = max(0, end - 1)
            if data[last : last + 1] == b"\n":
                end -= 1
            last = max(0, end - 1)
            if data[last : last + 1] == b"\r":
                end -= 1
            return end, next
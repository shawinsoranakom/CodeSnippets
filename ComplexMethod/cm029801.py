def mode(self):
        """String giving the file mode"""
        if self._created:
            if self._readable:
                return 'xb+'
            else:
                return 'xb'
        elif self._appending:
            if self._readable:
                return 'ab+'
            else:
                return 'ab'
        elif self._readable:
            if self._writable:
                if self._truncate:
                    return 'wb+'
                else:
                    return 'rb+'
            else:
                return 'rb'
        else:
            return 'wb'
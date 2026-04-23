def close_all(self, dsn: dict | str | None = None):
        count = 0
        last = None
        for i, cnx in tools.reverse_enumerate(self._connections):
            if dsn is None or self._dsn_equals(cnx.dsn, dsn):
                cnx.close()
                last = self._connections.pop(i)
                count += 1
        if count:
            _logger.info('%r: Closed %d connections %s', self, count,
                        (dsn and last and 'to %r' % last.dsn) or '')
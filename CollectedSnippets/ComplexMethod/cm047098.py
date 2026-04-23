def borrow(self, connection_info: dict) -> PsycoConnection:
        """
        Borrow a PsycoConnection from the pool. If no connection is available, create a new one
        as long as there are still slots available. Perform some garbage-collection in the pool:
        idle, dead and leaked connections are removed.

        :param dict connection_info: dict of psql connection keywords
        :rtype: PsycoConnection
        """
        # free idle, dead and leaked connections
        for i, cnx in tools.reverse_enumerate(self._connections):
            if not cnx._pool_in_use and not cnx.closed and time.time() - cnx._pool_last_used > MAX_IDLE_TIMEOUT:
                self._debug('Close connection at index %d: %r', i, cnx.dsn)
                cnx.close()
            if cnx.closed:
                self._connections.pop(i)
                self._debug('Removing closed connection at index %d: %r', i, cnx.dsn)
                continue
            if getattr(cnx, 'leaked', False):
                delattr(cnx, 'leaked')
                cnx._pool_in_use = False
                _logger.info('%r: Free leaked connection to %r', self, cnx.dsn)

        for i, cnx in enumerate(self._connections):
            if not cnx._pool_in_use and self._dsn_equals(cnx.dsn, connection_info):
                try:
                    cnx.reset()
                except psycopg2.OperationalError:
                    self._debug('Cannot reset connection at index %d: %r', i, cnx.dsn)
                    # psycopg2 2.4.4 and earlier do not allow closing a closed connection
                    if not cnx.closed:
                        cnx.close()
                    continue
                cnx._pool_in_use = True
                self._debug('Borrow existing connection to %r at index %d', cnx.dsn, i)

                return cnx

        if len(self._connections) >= self._maxconn:
            # try to remove the oldest connection not used
            for i, cnx in enumerate(self._connections):
                if not cnx._pool_in_use:
                    self._connections.pop(i)
                    if not cnx.closed:
                        cnx.close()
                    self._debug('Removing old connection at index %d: %r', i, cnx.dsn)
                    break
            else:
                # note: this code is called only if the for loop has completed (no break)
                raise PoolError('The Connection Pool Is Full')

        try:
            result = psycopg2.connect(
                connection_factory=PsycoConnection,
                **connection_info)
        except psycopg2.Error:
            _logger.info('Connection to the database failed')
            raise
        if result.server_version < MIN_PG_VERSION * 10000:
            warnings.warn(f"Postgres version is {result.server_version}, lower than minimum required {MIN_PG_VERSION * 10000}")
        result._pool_in_use = True
        self._connections.append(result)
        self._debug('Create new connection backend PID %d', result.get_backend_pid())

        return result
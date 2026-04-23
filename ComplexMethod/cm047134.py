def assertQueryCount(self, default=0, flush=True, **counters):
        """ Context manager that counts queries. It may be invoked either with
            one value, or with a set of named arguments like ``login=value``::

                with self.assertQueryCount(42):
                    ...

                with self.assertQueryCount(admin=3, demo=5):
                    ...

            The second form is convenient when used with :func:`users`.
        """
        if self.warm:
            # mock random in order to avoid random bus gc
            with patch('random.random', lambda: 1):
                login = self.env.user.login
                expected = counters.get(login, default)
                if flush:
                    self.env.flush_all()
                    self.env.cr.flush()
                count0 = self.cr.sql_log_count
                yield
                if flush:
                    self.env.flush_all()
                    self.env.cr.flush()
                count = self.cr.sql_log_count - count0
                if count != expected:
                    # add some info on caller to allow semi-automatic update of query count
                    _frame, filename, linenum, funcname, _lines, _index = inspect.stack()[2]
                    filename = filename.replace('\\', '/')
                    if "/odoo/addons/" in filename:
                        filename = filename.rsplit("/odoo/addons/", 1)[1]
                    if count > expected:
                        msg = "Query count more than expected for user %s: %d > %d in %s at %s:%s"
                        # add a subtest in order to continue the test_method in case of failures
                        with self.subTest():
                            self.fail(msg % (login, count, expected, funcname, filename, linenum))
                    else:
                        logger = logging.getLogger(type(self).__module__)
                        msg = "Query count less than expected for user %s: %d < %d in %s at %s:%s"
                        logger.info(msg, login, count, expected, funcname, filename, linenum)
        else:
            # flush before and after during warmup, in order to reproduce the
            # same operations, otherwise the caches might not be ready!
            if flush:
                self.env.flush_all()
                self.env.cr.flush()
            yield
            if flush:
                self.env.flush_all()
                self.env.cr.flush()
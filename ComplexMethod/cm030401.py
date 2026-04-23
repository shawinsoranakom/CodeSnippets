def _clean_tracebacks(self, exctype, value, tb, test):
        ret = None
        first = True
        excs = [(exctype, value, tb)]
        seen = {id(value)}  # Detect loops in chained exceptions.
        while excs:
            (exctype, value, tb) = excs.pop()
            # Skip test runner traceback levels
            while tb and self._is_relevant_tb_level(tb):
                tb = tb.tb_next

            # Skip assert*() traceback levels
            if exctype is test.failureException:
                self._remove_unittest_tb_frames(tb)

            if first:
                ret = tb
                first = False
            else:
                value.__traceback__ = tb

            if value is not None:
                for c in (value.__cause__, value.__context__):
                    if c is not None and id(c) not in seen:
                        excs.append((type(c), c, c.__traceback__))
                        seen.add(id(c))
        return ret
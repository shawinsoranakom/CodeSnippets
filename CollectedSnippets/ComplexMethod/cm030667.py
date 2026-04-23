def __exit__(self, type_=None, value=None, traceback=None):
        reset_Breakpoint()
        sys.settrace(self._original_tracer)

        not_empty = ''
        if self.tracer.set_list:
            not_empty += 'All paired tuples have not been processed, '
            not_empty += ('the last one was number %d\n' %
                          self.tracer.expect_set_no)
            not_empty += repr(self.tracer.set_list)

        # Make a BdbNotExpectedError a unittest failure.
        if type_ is not None and issubclass(BdbNotExpectedError, type_):
            if isinstance(value, BaseException) and value.args:
                err_msg = value.args[0]
                if not_empty:
                    err_msg += '\n' + not_empty
                if self.dry_run:
                    print(err_msg)
                    return True
                else:
                    self.test_case.fail(err_msg)
            else:
                assert False, 'BdbNotExpectedError with empty args'

        if not_empty:
            if self.dry_run:
                print(not_empty)
            else:
                self.test_case.fail(not_empty)
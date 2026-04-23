def getErrorCallerInfo(self, error, test):
        """
        :param error: A tuple (exctype, value, tb) as returned by sys.exc_info().
        :param test: A TestCase that created this error.
        :returns: a tuple (fn, lno, func, sinfo) matching the logger findCaller format or None
        """

        # only handle TestCase here. test can be an _ErrorHolder in some case (setup/teardown class errors)
        if not isinstance(test, case.TestCase):
            return

        _, _, error_traceback = error

        # move upwards the subtest hierarchy to find the real test
        while isinstance(test, case._SubTest) and test.test_case:
            test = test.test_case

        method_tb = None
        file_tb = None
        filename = inspect.getfile(type(test))

        # Note: since _ErrorCatcher was introduced, we could always take the
        # last frame, keeping the check on the test method for safety.
        # Fallbacking on file for cleanup file shoud always be correct to a
        # minimal working version would be
        #
        #   infos_tb = error_traceback
        #   while infos_tb.tb_next()
        #       infos_tb = infos_tb.tb_next()
        #
        while error_traceback:
            code = error_traceback.tb_frame.f_code
            if code.co_name in (test._testMethodName, 'setUp', 'tearDown'):
                method_tb = error_traceback
            if code.co_filename == filename:
                file_tb = error_traceback
            error_traceback = error_traceback.tb_next

        infos_tb = method_tb or file_tb
        if infos_tb:
            code = infos_tb.tb_frame.f_code
            lineno = infos_tb.tb_lineno
            filename = code.co_filename
            method = test._testMethodName
            return (filename, lineno, method, None)
def _complete_traceback(self, initial_tb):
        Traceback = type(initial_tb)

        # make the set of frames in the traceback
        tb_frames = set()
        tb = initial_tb
        while tb:
            tb_frames.add(tb.tb_frame)
            tb = tb.tb_next
        tb = initial_tb

        # find the common frame by searching the last frame of the current_stack present in the traceback.
        current_frame = inspect.currentframe()
        common_frame = None
        while current_frame:
            if current_frame in tb_frames:
                common_frame = current_frame  # we want to find the last frame in common
            current_frame = current_frame.f_back

        if not common_frame:  # not really useful but safer
            _logger.warning('No common frame found with current stack, displaying full stack')
            tb = initial_tb
        else:
            # remove the tb_frames until the common_frame is reached (keep the current_frame tb since the line is more accurate)
            while tb and tb.tb_frame != common_frame:
                tb = tb.tb_next

        # add all current frame elements under the common_frame to tb
        current_frame = common_frame.f_back
        while current_frame:
            tb = Traceback(tb, current_frame, current_frame.f_lasti, current_frame.f_lineno)
            current_frame = current_frame.f_back

        # remove traceback root part (odoo_bin, main, loading, ...), as
        # everything under the testCase is not useful. Using '_callTestMethod',
        # '_callSetUp', '_callTearDown', '_callCleanup' instead of the test
        # method since the error does not comme especially from the test method.
        while tb:
            code = tb.tb_frame.f_code
            if PurePath(code.co_filename).name == 'case.py' and code.co_name in ('_callTestMethod', '_callSetUp', '_callTearDown', '_callCleanup'):
                return tb.tb_next
            tb = tb.tb_next

        _logger.warning('No root frame found, displaying full stacks')
        return initial_tb
def check_error(self, code, lineno, fatal_error, *,
                    filename=None, all_threads=True, other_regex=None,
                    fd=None, know_current_thread=True,
                    py_fatal_error=False,
                    garbage_collecting=False,
                    c_stack=True,
                    function='<module>'):
        """
        Check that the fault handler for fatal errors is enabled and check the
        traceback from the child process output.

        Raise an error if the output doesn't match the expected format.
        """
        all_threads_disabled = (
            all_threads
            and (not sys._is_gil_enabled())
        )
        if all_threads and not all_threads_disabled:
            if know_current_thread:
                header = CURRENT_THREAD_HEADER
            else:
                header = THREAD_HEADER
        else:
            header = STACK_HEADER
        regex = [f'^{fatal_error}']
        if py_fatal_error:
            regex.append("Python runtime state: initialized")
        regex.append('')
        if all_threads_disabled and not py_fatal_error:
            regex.append("<Cannot show all threads while the GIL is disabled>")
        regex.append(fr'{header}')
        if support.Py_GIL_DISABLED and py_fatal_error and not know_current_thread:
            regex.append("  <tstate is freed>")
        else:
            if garbage_collecting and not all_threads_disabled:
                regex.append('  Garbage-collecting')
            regex.append(fr'  File "<string>", line {lineno} in {function}')
        if c_stack:
            regex.extend(C_STACK_REGEX)
        regex = '\n'.join(regex)

        if other_regex:
            regex = f'(?:{regex}|{other_regex})'

        # Enable MULTILINE flag
        regex = f'(?m){regex}'
        output, exitcode = self.get_output(code, filename=filename, fd=fd)
        output = '\n'.join(output)
        self.assertRegex(output, regex)
        self.assertNotEqual(exitcode, 0)
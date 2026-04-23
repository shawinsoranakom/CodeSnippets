def __run(self, test, compileflags, out):
        """
        Run the examples in `test`.  Write the outcome of each example
        with one of the `DocTestRunner.report_*` methods, using the
        writer function `out`.  `compileflags` is the set of compiler
        flags that should be used to execute examples.  Return a TestResults
        instance.  The examples are run in the namespace `test.globs`.
        """
        # Keep track of the number of failed, attempted, skipped examples.
        failures = attempted = skips = 0

        # Save the option flags (since option directives can be used
        # to modify them).
        original_optionflags = self.optionflags

        SUCCESS, FAILURE, BOOM = range(3) # `outcome` state

        check = self._checker.check_output

        # Process each example.
        for examplenum, example in enumerate(test.examples):
            attempted += 1

            # If REPORT_ONLY_FIRST_FAILURE is set, then suppress
            # reporting after the first failure.
            quiet = (self.optionflags & REPORT_ONLY_FIRST_FAILURE and
                     failures > 0)

            # Merge in the example's options.
            self.optionflags = original_optionflags
            if example.options:
                for (optionflag, val) in example.options.items():
                    if val:
                        self.optionflags |= optionflag
                    else:
                        self.optionflags &= ~optionflag

            # If 'SKIP' is set, then skip this example.
            if self.optionflags & SKIP:
                if not quiet:
                    self.report_skip(out, test, example)
                skips += 1
                continue

            # Record that we started this example.
            if not quiet:
                self.report_start(out, test, example)

            # Use a special filename for compile(), so we can retrieve
            # the source code during interactive debugging (see
            # __patched_linecache_getlines).
            filename = '<doctest %s[%d]>' % (test.name, examplenum)

            # Run the example in the given context (globs), and record
            # any exception that gets raised.  (But don't intercept
            # keyboard interrupts.)
            try:
                # Don't blink!  This is where the user's code gets run.
                exec(compile(example.source, filename, "single",
                             compileflags, True), test.globs)
                self.debugger.set_continue() # ==== Example Finished ====
                exc_info = None
            except KeyboardInterrupt:
                raise
            except BaseException as exc:
                exc_info = type(exc), exc, exc.__traceback__.tb_next
                self.debugger.set_continue() # ==== Example Finished ====

            got = self._fakeout.getvalue()  # the actual output
            self._fakeout.truncate(0)
            outcome = FAILURE   # guilty until proved innocent or insane

            # If the example executed without raising any exceptions,
            # verify its output.
            if exc_info is None:
                if check(example.want, got, self.optionflags):
                    outcome = SUCCESS

            # The example raised an exception:  check if it was expected.
            else:
                formatted_ex = traceback.format_exception_only(*exc_info[:2])
                if issubclass(exc_info[0], SyntaxError):
                    # SyntaxError / IndentationError is special:
                    # we don't care about the carets / suggestions / etc
                    # We only care about the error message and notes.
                    # They start with `SyntaxError:` (or any other class name)
                    exception_line_prefixes = (
                        f"{exc_info[0].__qualname__}:",
                        f"{exc_info[0].__module__}.{exc_info[0].__qualname__}:",
                    )
                    exc_msg_index = next(
                        index
                        for index, line in enumerate(formatted_ex)
                        if line.startswith(exception_line_prefixes)
                    )
                    formatted_ex = formatted_ex[exc_msg_index:]

                exc_msg = "".join(formatted_ex)
                if not quiet:
                    got += _exception_traceback(exc_info)

                # If `example.exc_msg` is None, then we weren't expecting
                # an exception.
                if example.exc_msg is None:
                    outcome = BOOM

                # We expected an exception:  see whether it matches.
                elif check(example.exc_msg, exc_msg, self.optionflags):
                    outcome = SUCCESS

                # Another chance if they didn't care about the detail.
                elif self.optionflags & IGNORE_EXCEPTION_DETAIL:
                    if check(_strip_exception_details(example.exc_msg),
                             _strip_exception_details(exc_msg),
                             self.optionflags):
                        outcome = SUCCESS

            # Report the outcome.
            if outcome is SUCCESS:
                if not quiet:
                    self.report_success(out, test, example, got)
            elif outcome is FAILURE:
                if not quiet:
                    self.report_failure(out, test, example, got)
                failures += 1
            elif outcome is BOOM:
                if not quiet:
                    self.report_unexpected_exception(out, test, example,
                                                     exc_info)
                failures += 1
            else:
                assert False, ("unknown outcome", outcome)

            if failures and self.optionflags & FAIL_FAST:
                break

        # Restore the option flags (in case they were modified)
        self.optionflags = original_optionflags

        # Record and return the number of failures and attempted.
        self.__record_outcome(test, failures, attempted, skips)
        return TestResults(failures, attempted, skipped=skips)
def handleError(self, record):
        """
        Handle errors which occur during an emit() call.

        This method should be called from handlers when an exception is
        encountered during an emit() call. If raiseExceptions is false,
        exceptions get silently ignored. This is what is mostly wanted
        for a logging system - most users will not care about errors in
        the logging system, they are more interested in application errors.
        You could, however, replace this with a custom handler if you wish.
        The record which was being processed is passed in to this method.
        """
        if raiseExceptions and sys.stderr:  # see issue 13807
            exc = sys.exception()
            try:
                sys.stderr.write('--- Logging error ---\n')
                traceback.print_exception(exc, limit=None, file=sys.stderr)
                sys.stderr.write('Call stack:\n')
                # Walk the stack frame up until we're out of logging,
                # so as to print the calling context.
                frame = exc.__traceback__.tb_frame
                while (frame and os.path.dirname(frame.f_code.co_filename) ==
                       __path__[0]):
                    frame = frame.f_back
                if frame:
                    traceback.print_stack(frame, file=sys.stderr)
                else:
                    # couldn't find the right stack frame, for some reason
                    sys.stderr.write('Logged from file %s, line %s\n' % (
                                     record.filename, record.lineno))
                # Issue 18671: output logging message and arguments
                try:
                    sys.stderr.write('Message: %r\n'
                                     'Arguments: %s\n' % (record.msg,
                                                          record.args))
                except RecursionError:  # See issue 36272
                    raise
                except Exception:
                    sys.stderr.write('Unable to print the message and arguments'
                                     ' - possible formatting error.\nUse the'
                                     ' traceback above to help find the error.\n'
                                    )
            except OSError: #pragma: no cover
                pass    # see issue 5971
            finally:
                del exc
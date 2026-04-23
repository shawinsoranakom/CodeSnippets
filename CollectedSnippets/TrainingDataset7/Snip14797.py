def get_traceback_frames(self):
        # Get the exception and all its causes
        exceptions = []
        exc_value = self.exc_value
        while exc_value:
            exceptions.append(exc_value)
            exc_value = self._get_explicit_or_implicit_cause(exc_value)
            if exc_value in exceptions:
                warnings.warn(
                    "Cycle in the exception chain detected: exception '%s' "
                    "encountered again." % exc_value,
                    ExceptionCycleWarning,
                )
                # Avoid infinite loop if there's a cyclic reference (#29393).
                break

        frames = []
        # No exceptions were supplied to ExceptionReporter
        if not exceptions:
            return frames

        # In case there's just one exception, take the traceback from self.tb
        exc_value = exceptions.pop()
        tb = self.tb if not exceptions else exc_value.__traceback__
        while True:
            frames.extend(self.get_exception_traceback_frames(exc_value, tb))
            try:
                exc_value = exceptions.pop()
            except IndexError:
                break
            tb = exc_value.__traceback__
        return frames
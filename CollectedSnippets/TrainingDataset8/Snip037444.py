def exception(self, exception: BaseException) -> "DeltaGenerator":
        """Display an exception.

        Parameters
        ----------
        exception : Exception
            The exception to display.

        Example
        -------
        >>> e = RuntimeError('This is an exception of type RuntimeError')
        >>> st.exception(e)

        """
        exception_proto = ExceptionProto()
        marshall(exception_proto, exception)
        return self.dg._enqueue("exception", exception_proto)
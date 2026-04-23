async def __aexit__(self, typ, value, traceback):
        if typ is None:
            try:
                await anext(self.gen)
            except StopAsyncIteration:
                return False
            else:
                try:
                    raise RuntimeError("generator didn't stop")
                finally:
                    await self.gen.aclose()
        else:
            if value is None:
                # Need to force instantiation so we can reliably
                # tell if we get the same exception back
                value = typ()
            try:
                await self.gen.athrow(value)
            except StopAsyncIteration as exc:
                # Suppress StopIteration *unless* it's the same exception that
                # was passed to throw().  This prevents a StopIteration
                # raised inside the "with" statement from being suppressed.
                return exc is not value
            except RuntimeError as exc:
                # Don't re-raise the passed in exception. (issue27122)
                if exc is value:
                    exc.__traceback__ = traceback
                    return False
                # Avoid suppressing if a Stop(Async)Iteration exception
                # was passed to athrow() and later wrapped into a RuntimeError
                # (see PEP 479 for sync generators; async generators also
                # have this behavior). But do this only if the exception wrapped
                # by the RuntimeError is actually Stop(Async)Iteration (see
                # issue29692).
                if (
                    isinstance(value, (StopIteration, StopAsyncIteration))
                    and exc.__cause__ is value
                ):
                    value.__traceback__ = traceback
                    return False
                raise
            except BaseException as exc:
                # only re-raise if it's *not* the exception that was
                # passed to throw(), because __exit__() must not raise
                # an exception unless __exit__() itself failed.  But throw()
                # has to raise the exception to signal propagation, so this
                # fixes the impedance mismatch between the throw() protocol
                # and the __exit__() protocol.
                if exc is not value:
                    raise
                exc.__traceback__ = traceback
                return False
            try:
                raise RuntimeError("generator didn't stop after athrow()")
            finally:
                await self.gen.aclose()
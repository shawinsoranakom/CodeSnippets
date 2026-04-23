def save_reduce(self, func, args, state=None, listitems=None,
                    dictitems=None, state_setter=None, *, obj=None):
        # This API is called by some subclasses

        if not callable(func):
            raise PicklingError(f"first item of the tuple returned by __reduce__ "
                                f"must be callable, not {_T(func)}")
        if not isinstance(args, tuple):
            raise PicklingError(f"second item of the tuple returned by __reduce__ "
                                f"must be a tuple, not {_T(args)}")

        save = self.save
        write = self.write

        func_name = getattr(func, "__name__", "")
        if self.proto >= 2 and func_name == "__newobj_ex__":
            cls, args, kwargs = args
            if not hasattr(cls, "__new__"):
                raise PicklingError("first argument to __newobj_ex__() has no __new__")
            if obj is not None and cls is not obj.__class__:
                raise PicklingError(f"first argument to __newobj_ex__() "
                                    f"must be {obj.__class__!r}, not {cls!r}")
            if self.proto >= 4:
                try:
                    save(cls)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} class')
                    raise
                try:
                    save(args)
                    save(kwargs)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} __new__ arguments')
                    raise
                write(NEWOBJ_EX)
            else:
                func = partial(cls.__new__, cls, *args, **kwargs)
                try:
                    save(func)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} reconstructor')
                    raise
                save(())
                write(REDUCE)
        elif self.proto >= 2 and func_name == "__newobj__":
            # A __reduce__ implementation can direct protocol 2 or newer to
            # use the more efficient NEWOBJ opcode, while still
            # allowing protocol 0 and 1 to work normally.  For this to
            # work, the function returned by __reduce__ should be
            # called __newobj__, and its first argument should be a
            # class.  The implementation for __newobj__
            # should be as follows, although pickle has no way to
            # verify this:
            #
            # def __newobj__(cls, *args):
            #     return cls.__new__(cls, *args)
            #
            # Protocols 0 and 1 will pickle a reference to __newobj__,
            # while protocol 2 (and above) will pickle a reference to
            # cls, the remaining args tuple, and the NEWOBJ code,
            # which calls cls.__new__(cls, *args) at unpickling time
            # (see load_newobj below).  If __reduce__ returns a
            # three-tuple, the state from the third tuple item will be
            # pickled regardless of the protocol, calling __setstate__
            # at unpickling time (see load_build below).
            #
            # Note that no standard __newobj__ implementation exists;
            # you have to provide your own.  This is to enforce
            # compatibility with Python 2.2 (pickles written using
            # protocol 0 or 1 in Python 2.3 should be unpicklable by
            # Python 2.2).
            cls = args[0]
            if not hasattr(cls, "__new__"):
                raise PicklingError("first argument to __newobj__() has no __new__")
            if obj is not None and cls is not obj.__class__:
                raise PicklingError(f"first argument to __newobj__() "
                                    f"must be {obj.__class__!r}, not {cls!r}")
            args = args[1:]
            try:
                save(cls)
            except BaseException as exc:
                exc.add_note(f'when serializing {_T(obj)} class')
                raise
            try:
                save(args)
            except BaseException as exc:
                exc.add_note(f'when serializing {_T(obj)} __new__ arguments')
                raise
            write(NEWOBJ)
        else:
            try:
                save(func)
            except BaseException as exc:
                exc.add_note(f'when serializing {_T(obj)} reconstructor')
                raise
            try:
                save(args)
            except BaseException as exc:
                exc.add_note(f'when serializing {_T(obj)} reconstructor arguments')
                raise
            write(REDUCE)

        if obj is not None:
            # If the object is already in the memo, this means it is
            # recursive. In this case, throw away everything we put on the
            # stack, and fetch the object back from the memo.
            if id(obj) in self.memo:
                write(POP + self.get(self.memo[id(obj)][0]))
            else:
                self.memoize(obj)

        # More new special cases (that work with older protocols as
        # well): when __reduce__ returns a tuple with 4 or 5 items,
        # the 4th and 5th item should be iterators that provide list
        # items and dict items (as (key, value) tuples), or None.

        if listitems is not None:
            self._batch_appends(listitems, obj)

        if dictitems is not None:
            self._batch_setitems(dictitems, obj)

        if state is not None:
            if state_setter is None:
                try:
                    save(state)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} state')
                    raise
                write(BUILD)
            else:
                # If a state_setter is specified, call it instead of load_build
                # to update obj's with its previous state.
                # First, push state_setter and its tuple of expected arguments
                # (obj, state) onto the stack.
                try:
                    save(state_setter)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} state setter')
                    raise
                save(obj)  # simple BINGET opcode as obj is already memoized.
                try:
                    save(state)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} state')
                    raise
                write(TUPLE2)
                # Trigger a state_setter(obj, state) function call.
                write(REDUCE)
                # The purpose of state_setter is to carry-out an
                # inplace modification of obj. We do not care about what the
                # method might return, so its output is eventually removed from
                # the stack.
                write(POP)
def save(self, obj, save_persistent_id=True):
        self.framer.commit_frame()

        # Check for persistent id (defined by a subclass)
        if save_persistent_id:
            pid = self.persistent_id(obj)
            if pid is not None:
                self.save_pers(pid)
                return

        # Check the memo
        x = self.memo.get(id(obj))
        if x is not None:
            self.write(self.get(x[0]))
            return

        rv = NotImplemented
        reduce = getattr(self, "reducer_override", _NoValue)
        if reduce is not _NoValue:
            rv = reduce(obj)

        if rv is NotImplemented:
            # Check the type dispatch table
            t = type(obj)
            f = self.dispatch.get(t)
            if f is not None:
                f(self, obj)  # Call unbound method with explicit self
                return

            # Check private dispatch table if any, or else
            # copyreg.dispatch_table
            reduce = getattr(self, 'dispatch_table', dispatch_table).get(t, _NoValue)
            if reduce is not _NoValue:
                rv = reduce(obj)
            else:
                # Check for a class with a custom metaclass; treat as regular
                # class
                if issubclass(t, type):
                    self.save_global(obj)
                    return

                # Check for a __reduce_ex__ method, fall back to __reduce__
                reduce = getattr(obj, "__reduce_ex__", _NoValue)
                if reduce is not _NoValue:
                    rv = reduce(self.proto)
                else:
                    reduce = getattr(obj, "__reduce__", _NoValue)
                    if reduce is not _NoValue:
                        rv = reduce()
                    else:
                        raise PicklingError(f"Can't pickle {_T(t)} object")

        # Check for string returned by reduce(), meaning "save as global"
        if isinstance(rv, str):
            self.save_global(obj, rv)
            return

        try:
            # Assert that reduce() returned a tuple
            if not isinstance(rv, tuple):
                raise PicklingError(f'__reduce__ must return a string or tuple, not {_T(rv)}')

            # Assert that it returned an appropriately sized tuple
            l = len(rv)
            if not (2 <= l <= 6):
                raise PicklingError("tuple returned by __reduce__ "
                                    "must contain 2 through 6 elements")

            # Save the reduce() output and finally memoize the object
            self.save_reduce(obj=obj, *rv)
        except BaseException as exc:
            exc.add_note(f'when serializing {_T(obj)} object')
            raise
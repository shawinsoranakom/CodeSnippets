def save_tuple(self, obj):
        if not obj: # tuple is empty
            if self.bin:
                self.write(EMPTY_TUPLE)
            else:
                self.write(MARK + TUPLE)
            return

        n = len(obj)
        save = self.save
        memo = self.memo
        if n <= 3 and self.proto >= 2:
            for i, element in enumerate(obj):
                try:
                    save(element)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} item {i}')
                    raise
            # Subtle.  Same as in the big comment below.
            if id(obj) in memo:
                get = self.get(memo[id(obj)][0])
                self.write(POP * n + get)
            else:
                self.write(_tuplesize2code[n])
                self.memoize(obj)
            return

        # proto 0 or proto 1 and tuple isn't empty, or proto > 1 and tuple
        # has more than 3 elements.
        write = self.write
        write(MARK)
        for i, element in enumerate(obj):
            try:
                save(element)
            except BaseException as exc:
                exc.add_note(f'when serializing {_T(obj)} item {i}')
                raise

        if id(obj) in memo:
            # Subtle.  d was not in memo when we entered save_tuple(), so
            # the process of saving the tuple's elements must have saved
            # the tuple itself:  the tuple is recursive.  The proper action
            # now is to throw away everything we put on the stack, and
            # simply GET the tuple (it's already constructed).  This check
            # could have been done in the "for element" loop instead, but
            # recursive tuples are a rare thing.
            get = self.get(memo[id(obj)][0])
            if self.bin:
                write(POP_MARK + get)
            else:   # proto 0 -- POP_MARK not available
                write(POP * (n+1) + get)
            return

        # No recursion.
        write(TUPLE)
        self.memoize(obj)
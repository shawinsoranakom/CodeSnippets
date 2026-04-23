def next_set_method(self):
        set_type = self.set_tuple[0]
        args = self.set_tuple[1] if len(self.set_tuple) == 2 else None
        set_method = getattr(self, 'set_' + set_type)

        # The following set methods give back control to the tracer.
        if set_type in ('step', 'stepinstr', 'continue', 'quit'):
            set_method()
            return
        elif set_type in ('next', 'return'):
            set_method(self.frame)
            return
        elif set_type == 'until':
            lineno = None
            if args:
                lineno = self.lno_rel2abs(self.frame.f_code.co_filename,
                                          args[0])
            set_method(self.frame, lineno)
            return

        # The following set methods do not give back control to the tracer and
        # next_set_method() is called recursively.
        if (args and set_type in ('break', 'clear', 'ignore', 'enable',
                                    'disable')) or set_type in ('up', 'down'):
            if set_type in ('break', 'clear'):
                fname, lineno, *remain = args
                lineno = self.lno_rel2abs(fname, lineno)
                args = [fname, lineno]
                args.extend(remain)
                set_method(*args)
            elif set_type in ('ignore', 'enable', 'disable'):
                set_method(*args)
            elif set_type in ('up', 'down'):
                set_method()

            # Process the next expect_set item.
            # It is not expected that a test may reach the recursion limit.
            self.event= None
            self.pop_next()
            if self.dry_run:
                self.print_state()
            else:
                if self.expect:
                    self.check_lno_name()
                self.check_expect_max_size(3)
            self.next_set_method()
        else:
            raise BdbSyntaxError('"%s" is an invalid set_tuple' %
                                 self.set_tuple)
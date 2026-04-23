def process_event(self, event, frame, *args):
        # Call get_stack() to enable walking the stack with set_up() and
        # set_down().
        tb = None
        if event == 'exception':
            tb = self.exc_info[2]
        self.get_stack(frame, tb)

        # A breakpoint has been hit and it is not a temporary.
        if self.currentbp is not None and not self.breakpoint_hits:
            bp_list = [self.currentbp]
            self.breakpoint_hits = (bp_list, [])

        # Pop next event.
        self.event= event
        self.pop_next()
        if self.dry_run:
            self.print_state(self.header)
            return

        # Validate the expected results.
        if self.expect:
            self.check_equal(self.expect[0], event, 'Wrong event type')
            self.check_lno_name()

        if event in ('call', 'return'):
            self.check_expect_max_size(3)
        elif len(self.expect) > 3:
            if event == 'line':
                bps, temporaries = self.expect[3]
                bpnums = sorted(bps.keys())
                if not self.breakpoint_hits:
                    self.raise_not_expected(
                        'No breakpoints hit at expect_set item %d' %
                        self.expect_set_no)
                self.check_equal(bpnums, self.breakpoint_hits[0],
                    'Breakpoint numbers do not match')
                self.check_equal([bps[n] for n in bpnums],
                    [self.get_bpbynumber(n).hits for
                        n in self.breakpoint_hits[0]],
                    'Wrong breakpoint hit count')
                self.check_equal(sorted(temporaries), self.breakpoint_hits[1],
                    'Wrong temporary breakpoints')

            elif event == 'exception':
                if not isinstance(self.exc_info[1], self.expect[3]):
                    self.raise_not_expected(
                        "Wrong exception at expect_set item %d, got '%s'" %
                        (self.expect_set_no, self.exc_info))
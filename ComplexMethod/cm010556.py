def _set_backward_stacktraces(self):
        def bw_parent(evt):
            if evt is None:
                return None
            elif evt.scope == 1:  # BACKWARD_FUNCTION
                return evt
            else:
                return bw_parent(evt.cpu_parent)

        fwd_stacks = {}
        for evt in self:
            if bw_parent(evt) is None and evt.stack is not None:
                t = (evt.sequence_nr, evt.thread)
                if t not in fwd_stacks:
                    fwd_stacks[t] = evt.stack

        for evt in self:
            p = bw_parent(evt)
            if p is not None:
                if p.fwd_thread is None:
                    raise AssertionError(
                        "Expected fwd_thread to be set for backward parent"
                    )
                t = (p.sequence_nr, p.fwd_thread)
                evt.stack = fwd_stacks.get(t, [])
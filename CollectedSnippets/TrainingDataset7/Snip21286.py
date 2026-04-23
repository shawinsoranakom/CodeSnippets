def make_id(target):
            """
            Simulate id() reuse for distinct senders with non-overlapping
            lifetimes that would require memory contention to reproduce.
            """
            if isinstance(target, Sender):
                return 0
            return _make_id(target)
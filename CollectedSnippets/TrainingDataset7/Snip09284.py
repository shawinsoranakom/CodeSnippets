def for_update_sql(self, nowait=False, skip_locked=False, of=(), no_key=False):
        """
        Return the FOR UPDATE SQL clause to lock rows for an update operation.
        """
        return "FOR%s UPDATE%s%s%s" % (
            " NO KEY" if no_key else "",
            " OF %s" % ", ".join(of) if of else "",
            " NOWAIT" if nowait else "",
            " SKIP LOCKED" if skip_locked else "",
        )
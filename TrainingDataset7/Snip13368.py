def __repr__(self):
        reversed_text = " reversed" if self.is_reversed else ""
        return "<%s: for %s in %s, tail_len: %d%s>" % (
            self.__class__.__name__,
            ", ".join(self.loopvars),
            self.sequence,
            len(self.nodelist_loop),
            reversed_text,
        )
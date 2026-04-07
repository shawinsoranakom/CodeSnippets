def __init__(
        self, loopvars, sequence, is_reversed, nodelist_loop, nodelist_empty=None
    ):
        self.loopvars = loopvars
        self.sequence = sequence
        self.is_reversed = is_reversed
        self.nodelist_loop = nodelist_loop
        if nodelist_empty is None:
            self.nodelist_empty = NodeList()
        else:
            self.nodelist_empty = nodelist_empty
def __init__(self, nodelist_true, nodelist_false, *varlist):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self._varlist = varlist
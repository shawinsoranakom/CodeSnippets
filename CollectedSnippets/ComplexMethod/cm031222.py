def _setup(self, master, cnf):
        """Internal function. Sets up information about children."""
        if master is None:
            master = _get_default_root()
        self.master = master
        self.tk = master.tk
        name = None
        if 'name' in cnf:
            name = cnf['name']
            del cnf['name']
        if not name:
            name = self.__class__.__name__.lower()
            if name[-1].isdigit():
                name += "!"  # Avoid duplication when calculating names below
            if master._last_child_ids is None:
                master._last_child_ids = {}
            count = master._last_child_ids.get(name, 0) + 1
            master._last_child_ids[name] = count
            if count == 1:
                name = '!%s' % (name,)
            else:
                name = '!%s%d' % (name, count)
        self._name = name
        if master._w=='.':
            self._w = '.' + name
        else:
            self._w = master._w + '.' + name
        self.children = {}
        if self._name in self.master.children:
            self.master.children[self._name].destroy()
        self.master.children[self._name] = self
def _fill_table(self):
        selected_row = self._table.selected_row()
        self._table.clear()
        if self._tab == "all packages":
            items = self._ds.packages()
        elif self._tab == "corpora":
            items = self._ds.corpora()
        elif self._tab == "models":
            items = self._ds.models()
        elif self._tab == "collections":
            items = self._ds.collections()
        else:
            assert 0, "bad tab value %r" % self._tab
        rows = [self._package_to_columns(item) for item in items]
        self._table.extend(rows)

        # Highlight the active tab.
        for tab, label in self._tabs.items():
            if tab == self._tab:
                label.configure(
                    foreground=self._FRONT_TAB_COLOR[0],
                    background=self._FRONT_TAB_COLOR[1],
                )
            else:
                label.configure(
                    foreground=self._BACK_TAB_COLOR[0],
                    background=self._BACK_TAB_COLOR[1],
                )

        self._table.sort_by("Identifier", order="ascending")
        self._color_table()
        self._table.select(selected_row)

        # This is a hack, because the scrollbar isn't updating its
        # position right -- I'm not sure what the underlying cause is
        # though.  (This is on OS X w/ python 2.5)  The length of
        # delay that's necessary seems to depend on how fast the
        # comptuer is. :-/
        self.top.after(150, self._table._scrollbar.set, *self._table._mlb.yview())
        self.top.after(300, self._table._scrollbar.set, *self._table._mlb.yview())
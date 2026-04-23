def search_next(self, *, forwards: bool) -> None:
        """Search history for the current line contents up to the cursor.

        Selects the first item found. If nothing is under the cursor, any next
        item in history is selected.
        """
        pos = self.pos
        s = self.get_unicode()
        history_index = self.historyi

        # In multiline contexts, we're only interested in the current line.
        nl_index = s.rfind('\n', 0, pos)
        prefix = s[nl_index + 1:pos]
        pos = len(prefix)

        match_prefix = len(prefix)
        len_item = 0
        if history_index < len(self.history):
            len_item = len(self.get_item(history_index))
        if len_item and pos == len_item:
            match_prefix = False
        elif not pos:
            match_prefix = False

        while 1:
            if forwards:
                out_of_bounds = history_index >= len(self.history) - 1
            else:
                out_of_bounds = history_index == 0
            if out_of_bounds:
                if forwards and not match_prefix:
                    self.pos = 0
                    self.buffer = []
                    self.invalidate_buffer(0)
                else:
                    self.error("not found")
                return

            history_index += 1 if forwards else -1
            s = self.get_item(history_index)

            if not match_prefix:
                self.select_item(history_index)
                return

            len_acc = 0
            for i, line in enumerate(s.splitlines(keepends=True)):
                if line.startswith(prefix):
                    self.select_item(history_index)
                    self.pos = pos + len_acc
                    return
                len_acc += len(line)
def start_loop(self) -> t.Generator[tuple[int, object]]:
        self._loop_var = loop_var = t.cast(str, self.task.loop_control.loop_var)
        self._index_var = index_var = t.cast(str, self.task.loop_control.index_var)

        extended = t.cast(bool, self.task.loop_control.extended)
        extended_allitems = t.cast(bool, self.task.loop_control.extended_allitems)

        items = self._loop_items
        items_len = len(items)

        for item_index, item in enumerate(self._loop_items):
            self._active_task_vars = self._base_task_vars.copy()  # isolate changes to task vars between loop items
            self._templar = None  # we're changing the values used to calculate the templar, null it out so the next requester re-creates it

            self._item = item
            self._item_index = item_index

            loop_vars: dict[str, object] = dict(
                ansible_loop_var=loop_var,
            )

            loop_vars[loop_var] = item

            if index_var:
                loop_vars['ansible_index_var'] = index_var
                loop_vars[index_var] = item_index

            if extended:
                ansible_loop: dict[str, object] = {
                    'index': item_index + 1,
                    'index0': item_index,
                    'first': item_index == 0,
                    'last': item_index + 1 == items_len,
                    'length': items_len,
                    'revindex': items_len - item_index,
                    'revindex0': items_len - item_index - 1,
                }

                if extended_allitems:
                    ansible_loop['allitems'] = items

                try:
                    ansible_loop['nextitem'] = items[item_index + 1]
                except IndexError:
                    pass

                if item_index - 1 >= 0:
                    ansible_loop['previtem'] = items[item_index - 1]

                self._loop_extended = loop_vars['ansible_loop'] = ansible_loop

            self.task_vars.update(loop_vars)

            yield item_index, item

            if self._break_when_triggered:
                break

        self._has_loop_exited = True
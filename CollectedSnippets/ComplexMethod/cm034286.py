def _record_result(self, utr: UnifiedTaskResult) -> None:
        # CAUTION: This method can be called *before* start_loop when validation errors occur.
        #          That results in various instance attributes not being set.
        #          It also means that `self.task.loop_control` may have invalid values.

        self._enable_registered_vars()

        if isinstance(self.task.ignore_errors, bool):
            # HACK: avoid setting to True due to template failures -- this should go away once field attribute templating is fixed
            utr.ignore_errors = self.task.ignore_errors

        if isinstance(self.task.ignore_unreachable, bool):
            # HACK: avoid setting to True due to template failures -- this should go away once field attribute templating is fixed
            utr.ignore_unreachable = self.task.ignore_unreachable

        # _item_index will be None if start_loop was not called due to a field attribute error
        if not TaskContext.current().is_loop or self._item_index is None:
            self._raw_loop_results.clear()
            self._raw_loop_results.append(utr)

            return

        if TaskContext.current().has_loop_exited:
            return

        # now update the result with the item info, and append the result
        # to the list of results
        utr.loop_item = self._item
        utr.loop_var = self._loop_var
        utr.loop_extended = self._loop_extended

        if self._index_var:
            utr.loop_index = self._item_index
            utr.loop_index_var = self._index_var

        item_index = self._item_index
        result_count = len(self._raw_loop_results)

        if item_index == result_count:
            self._raw_loop_results.append(utr)  # add new result
        elif item_index + 1 == result_count:
            self._raw_loop_results[item_index] = utr  # replace existing result
        else:
            raise RuntimeError(f'Item index {item_index} does not match {result_count}.')

        self._populate_item_label(utr)
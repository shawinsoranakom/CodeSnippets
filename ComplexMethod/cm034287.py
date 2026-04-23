def build_loop_result(self, preview: bool = False) -> UnifiedTaskResult:
        if not self.is_loop:
            raise NotALoopError()

        if not preview and (self._item_index is None or len(self._raw_loop_results) not in (self._item_index, self._item_index + 1)):
            # RPFIX-9: FUTURE: can we ditch preview while retaining this safety check?
            # Loop results can be queried before or after loop results are recorded, so we need to accept a range of results.
            raise RuntimeError(f"Mismatch between item index {self._item_index} and loop result count {len(self._raw_loop_results)}.")

        # create the overall result item
        utr = UnifiedTaskResult.from_action_result_dict()
        utr.loop_results = self._raw_loop_results

        # RPFIX-5: IMPL: all the fields set in this loop could be converted to properties
        for item in self._raw_loop_results:
            if item.no_log:
                utr.no_log = True  # ensure no_log processing recognizes at least one item needs to be censored

            utr._extend_warnings(item.warnings)
            utr._extend_deprecations(item.deprecations)

        if all(item.skipped for item in self._raw_loop_results):
            utr.set_skipped()
            utr.msg = 'All items skipped'
        elif utr.failed:
            utr.msg = 'One or more items failed'
        else:
            utr.msg = 'All items completed'

        return utr
def add_inspection_data(self, env: TestStateEnvironment):
        if self._wrapped.query_language.query_language_mode == QueryLanguageMode.JSONPath:
            if "afterResultSelector" not in env.inspection_data:
                # HACK: A DistributedItemProcessorEvalInput is added to the stack and never popped off
                # during an error case. So we need to check the inspected value is correct before
                # adding it to our inspectionData.
                if isinstance(env.stack[-1], (dict, str, int, float, list)):
                    env.inspection_data["afterResultSelector"] = to_json_str(env.stack[-1])

        if catch := self._wrapped.catch:
            for ind, catcher in enumerate(catch.catchers):
                original_fn = catcher._eval_body
                catcher._eval_body = self.with_catch_state_id(original_fn, ind)

        if retry := self._wrapped.retry:
            for ind, retrier in enumerate(retry.retriers):
                original_fn = retrier._eval_body
                retrier._eval_body = self.with_retry_state_id(retrier, ind)
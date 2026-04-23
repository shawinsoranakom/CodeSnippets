def _keep_test(self, test_case):
        # TODO: consider regex matching for test filtering.
        # Currently, this is a sub-string matching.
        op_test_config = test_case.test_config

        operators = (
            benchmark_utils.process_arg_list(self.args.operators)
            if self.args.operators
            else None
        )

        # Filter framework, operator, test_name, tag, forward_only
        return (
            self._check_keep(op_test_config.test_name, self.args.test_name)
            and self._check_keep_list(test_case.op_bench.module_name(), operators)
            and self._check_skip(test_case.op_bench.module_name(), SKIP_OP_LISTS)
            and self._check_operator_first_char(
                test_case.op_bench.module_name(), self.operator_range
            )
            and (
                self.args.tag_filter == "all"
                or self._check_keep(op_test_config.tag, self.args.tag_filter)
            )
            and (
                not self.args.forward_only
                or op_test_config.run_backward != self.args.forward_only
            )
            and (
                self.args.device == "None"
                or "device" not in test_case.test_config.input_config
                or self.args.device in op_test_config.test_name
            )
        )
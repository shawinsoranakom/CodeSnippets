def _check_results(self, opt, opts, check_items=False):
        self.assertEqual(len(opts), 1, f"Expected 1 optimizer: len(opts): {len(opts)}")
        self.assertEqual(
            id(opt),
            opts[0].self_ptr,
            f"Optimizer addr ({id(opt)}) vs. profiled addr ({opts[0].self_ptr})",
        )
        if check_items:
            self.assertEqual(len(opt.param_groups), len(opts))
            for group, opt_ in zip(opt.param_groups, opts):
                self.assertEqual(
                    [(v.storage().data_ptr()) for v in group.get("params", [])],
                    [(o.storage_data_ptr) for (o, _, _) in opt_.parameters],
                )
            for opt_ in opts:
                observed_state = {
                    p.storage_data_ptr: {name: s.storage_data_ptr for name, s in state}
                    for (p, _, state) in opt_.parameters
                }

                # Make sure the profiler collected all optimizer state and check
                # that the address recorded by the profiler is correct.
                for parameter, parameter_state in opt.state.items():
                    self.assertEqual(
                        {
                            name: value.storage().data_ptr()
                            for name, value in parameter_state.items()
                        },
                        observed_state.get(parameter.storage().data_ptr(), []),
                    )
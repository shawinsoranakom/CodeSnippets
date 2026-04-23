def run_one_model(
        self,
        name,
        model,
        example_inputs,
        optimize_ctx,
        experiment,
        explain=False,
        tag=None,
        batch_size=None,
    ):
        mode = "train" if self.args.training else "eval"
        msg = f"{current_device:4} {mode:5} {current_name:34} "
        if tag:
            msg += f" {tag:26}"
        print(msg, flush=True)

        start_stats = get_dynamo_stats()

        if self.args.accuracy:
            if self.args.batch_invariant:
                status = self.check_batch_invariance(
                    name, model, example_inputs, optimize_ctx, experiment, tag
                )
            else:
                status = self.check_accuracy(
                    name, model, example_inputs, optimize_ctx, experiment, tag
                )
            print(status)
            if status == "fail_accuracy" and self.args.minify:
                self.minify_model(
                    name, model, example_inputs, optimize_ctx, experiment, tag
                )
        elif self.args.tolerance:
            status = self.check_tolerance(name, model, example_inputs, optimize_ctx)
            print(status)
        elif self.args.performance:
            if self.args.backend in ["torchao", "optimus"]:
                status = self.run_performance_test_non_alternate(
                    name, model, example_inputs, optimize_ctx, experiment, tag
                )
            else:
                status = self.run_performance_test(
                    name,
                    model,
                    example_inputs,
                    optimize_ctx,
                    experiment,
                    tag,
                    batch_size=batch_size,
                )
            print(status)
        empty_gpu_cache(current_device)

        self.maybe_preserve_compile_debug(name, status)

        if self.args.timing:
            from torch._dynamo.utils import op_count, print_time_report
            from torch.utils._stats import simple_call_counter

            print_time_report()
            stats = "STATS: "
            stats = stats + " | ".join(
                itertools.chain(
                    [f"call_* op count: {op_count}"],
                    (f"{key}:{value}" for key, value in simple_call_counter.items()),
                )
            )
            print(stats)
        stats = get_dynamo_stats()
        stats.subtract(start_stats)

        if explain:
            print(
                f"Dynamo produced {stats['unique_graphs']} graphs "
                f"covering {stats['calls_captured']} ops with "
                f"{stats['graph_breaks']} graph breaks ({stats['unique_graph_breaks']} unique)"
            )

        if explain or self.args.log_graph_breaks or self.args.print_graph_breaks:
            filename = f"{output_filename.rstrip('.csv')}_graph_breaks.csv"

            def add_double_quotes(x):
                # Delimiter because reason could have comma
                return f'"{x}"'

            for graph_break in graph_break_reasons:
                reason = add_double_quotes(graph_break.reason)
                user_stack = add_double_quotes(
                    ", ".join([str(x) for x in graph_break.user_stack])
                )

                # NB: Don't upload them to the benchmark database as they are debugging
                # information. There are also around a million records a day which is
                # wasteful to store
                write_outputs(
                    filename,
                    ["model", "reason", "user_stack"],
                    [current_name, reason, user_stack],
                    False,
                )

        if self.args.stats:
            Stats.print_summary()
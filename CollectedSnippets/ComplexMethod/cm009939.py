def _collect_metrics(self) -> tuple[dict[str, _RowResult], dict[str, Run]]:
        all_eval_results: dict = {}
        all_runs: dict = {}
        for c in self.configs:
            for callback in cast("list", c["callbacks"]):
                if isinstance(callback, EvaluatorCallbackHandler):
                    eval_results = callback.logged_eval_results
                    for (_, example_id), v in eval_results.items():
                        all_eval_results.setdefault(str(example_id), {}).update(
                            {"feedback": v},
                        )
                elif isinstance(callback, LangChainTracer):
                    run = callback.latest_run
                    execution_time = (
                        (run.end_time - run.start_time).total_seconds()
                        if run and run.end_time
                        else None
                    )
                    run_id = str(run.id) if run else None
                    all_eval_results.setdefault(str(callback.example_id), {}).update(
                        {
                            "execution_time": execution_time,
                            "run_id": run_id,
                            "run": run,
                        },
                    )
                    all_runs[str(callback.example_id)] = run
        return cast("dict[str, _RowResult]", all_eval_results), all_runs
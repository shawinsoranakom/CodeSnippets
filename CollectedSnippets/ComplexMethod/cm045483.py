async def tabulate_results(self, run_ids: List[str], include_reasons: bool = False) -> TabulatedResults:
        """
        Generate a tabular representation of evaluation results across runs.

        This method collects scores across different runs and organizes them by
        dimension, making it easy to create visualizations like radar charts.

        Args:
            run_ids: List of run IDs to include in the tabulation
            include_reasons: Whether to include scoring reasons in the output

        Returns:
            A dictionary with structured data suitable for visualization
        """
        result: TabulatedResults = {"dimensions": [], "runs": []}

        # Parallelize fetching of run configs and scores
        fetch_tasks = []
        for run_id in run_ids:
            fetch_tasks.append(self._get_run_config(run_id))
            fetch_tasks.append(self.get_run_score(run_id))

        # Wait for all fetches to complete
        fetch_results = await asyncio.gather(*fetch_tasks)

        # Process fetched data
        dimensions_set = set()
        run_data = {}

        for i in range(0, len(fetch_results), 2):
            run_id = run_ids[i // 2]
            run_config = fetch_results[i]
            score = fetch_results[i + 1]

            # Store run data for later processing
            run_data[run_id] = (run_config, score)

            # Collect dimensions
            if score and score.dimension_scores:
                for dim_score in score.dimension_scores:
                    dimensions_set.add(dim_score.dimension)

        # Convert dimensions to sorted list
        result["dimensions"] = sorted(list(dimensions_set))

        # Process each run's data
        for run_id, (run_config, score) in run_data.items():
            if not run_config or not score:
                continue

            # Determine runner type
            runner_type = "unknown"
            if run_config.get("runner_config"):
                runner_config = run_config.get("runner_config")
                if runner_config is not None and "provider" in runner_config:
                    if "ModelEvalRunner" in runner_config["provider"]:
                        runner_type = "model"
                    elif "TeamEvalRunner" in runner_config["provider"]:
                        runner_type = "team"

            # Get task name
            task = run_config.get("task")
            task_name = task.name if task else "Unknown Task"

            # Create run entry
            run_entry: RunEntry = {
                "id": run_id,
                "name": run_config.get("name", f"Run {run_id}"),
                "task_name": task_name,
                "runner_type": runner_type,
                "overall_score": score.overall_score,
                "scores": [],
                "reasons": [] if include_reasons else None,
            }

            # Build dimension lookup map for O(1) access
            dim_map = {ds.dimension: ds for ds in score.dimension_scores}

            # Populate scores aligned with dimensions
            for dim in result["dimensions"]:
                dim_score = dim_map.get(dim)
                if dim_score:
                    run_entry["scores"].append(dim_score.score)
                    if include_reasons:
                        run_entry["reasons"].append(dim_score.reason)  # type: ignore
                else:
                    run_entry["scores"].append(None)
                    if include_reasons:
                        run_entry["reasons"].append(None)  # type: ignore

            result["runs"].append(run_entry)

        return result
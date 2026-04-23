async def _execute_run(self, run_id: str) -> None:
        """
        Execute an evaluation run.

        Args:
            run_id: The ID of the run to execute
        """
        try:
            # Get run configuration
            run_config = await self._get_run_config(run_id)
            if not run_config:
                raise ValueError(f"Run not found: {run_id}")

            # Get task
            task = run_config.get("task")
            if not task:
                raise ValueError(f"Task not found for run: {run_id}")

            # Initialize runner
            runner_config = run_config.get("runner_config")
            runner = BaseEvalRunner.load_component(runner_config) if runner_config else None

            # Initialize judge
            judge_config = run_config.get("judge_config")
            judge = BaseEvalJudge.load_component(judge_config) if judge_config else None

            if not runner or not judge:
                raise ValueError(f"Runner or judge not found for run: {run_id}")

            # Initialize criteria
            criteria_configs = run_config.get("criteria_configs")
            criteria = []
            if criteria_configs:
                criteria = [
                    EvalJudgeCriteria.model_validate(c) if not isinstance(c, EvalJudgeCriteria) else c
                    for c in criteria_configs
                ]

            # Execute runner
            logger.info(f"Starting runner for run {run_id}")
            start_time = datetime.now()
            run_result = await runner.run(task)

            # Update run result
            await self._update_run_result(run_id, run_result)

            if not run_result.status:
                logger.error(f"Runner failed for run {run_id}: {run_result.error}")
                await self._update_run_status(run_id, EvalRunStatus.FAILED)
                return

            # Execute judge
            logger.info(f"Starting judge for run {run_id}")
            score_result = await judge.judge(task, run_result, criteria)

            # Update score result
            await self._update_score_result(run_id, score_result)

            # Update run status
            end_time = datetime.now()
            await self._update_run_completed(run_id, start_time, end_time)

            logger.info(f"Run {run_id} completed successfully")

        except Exception as e:
            logger.exception(f"Error executing run {run_id}: {str(e)}")
            await self._update_run_error(run_id, str(e))
        finally:
            # Remove from active runs
            if run_id in self._active_runs:
                del self._active_runs[run_id]
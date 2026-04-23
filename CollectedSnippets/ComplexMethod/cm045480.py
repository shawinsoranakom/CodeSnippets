async def create_run(
        self,
        task: Union[str, EvalTask],
        runner: BaseEvalRunner,
        judge: BaseEvalJudge,
        criteria: List[Union[str, EvalJudgeCriteria]],
        name: str = "",
        description: str = "",
    ) -> str:
        """
        Create a new evaluation run configuration.

        Args:
            task: The task to evaluate (ID or task object)
            runner: The runner to use for evaluation
            judge: The judge to use for evaluation
            criteria: List of criteria to use for evaluation (IDs or criteria objects)
            name: Name for the run
            description: Description for the run

        Returns:
            Run ID
        """
        # Resolve task
        task_obj = None
        if isinstance(task, str):
            task_obj = await self.get_task(task)
            if not task_obj:
                raise ValueError(f"Task not found: {task}")
        else:
            task_obj = task

        # Resolve criteria
        criteria_objs = []
        for criterion in criteria:
            if isinstance(criterion, str):
                criterion_obj = await self.get_criteria(criterion)
                if not criterion_obj:
                    raise ValueError(f"Criteria not found: {criterion}")
                criteria_objs.append(criterion_obj)
            else:
                criteria_objs.append(criterion)

        # Generate run ID
        run_id = str(uuid.uuid4())

        # Create run configuration
        runner_config = runner.dump_component() if hasattr(runner, "dump_component") else runner._to_config()
        judge_config = judge.dump_component() if hasattr(judge, "dump_component") else judge._to_config()

        if self._db_manager:
            # Store in database
            run_db = EvalRunDB(
                name=name or f"Run {run_id}",
                description=description,
                task_id=int(task) if isinstance(task, str) and task.isdigit() else None,
                runner_config=runner_config.model_dump(),
                judge_config=judge_config.model_dump(),
                criteria_configs=criteria_objs,
                status=EvalRunStatus.PENDING,
            )
            response = self._db_manager.upsert(run_db)
            if not response.status:
                logger.error(f"Failed to store run: {response.message}")
                raise RuntimeError(f"Failed to store run: {response.message}")
            run_id = str(response.data.get("id")) if response.data else run_id
        else:
            # Store in memory
            self._runs[run_id] = {
                "task": task_obj,
                "runner_config": runner_config,
                "judge_config": judge_config,
                "criteria_configs": [c.model_dump() for c in criteria_objs],
                "status": EvalRunStatus.PENDING,
                "created_at": datetime.now(),
                "run_result": None,
                "score_result": None,
                "name": name or f"Run {run_id}",
                "description": description,
            }

        return run_id
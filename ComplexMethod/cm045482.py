async def _get_run_config(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration of an evaluation run.

        Args:
            run_id: The ID of the run

        Returns:
            The run configuration if found, None otherwise
        """
        if self._db_manager:
            # Retrieve from database
            response = self._db_manager.get(EvalRunDB, filters={"id": int(run_id) if run_id.isdigit() else run_id})

            if response.status and response.data and len(response.data) > 0:
                run_data = response.data[0]

                # Get task
                task = None
                if run_data.get("task_id"):
                    task_response = self._db_manager.get(EvalTaskDB, filters={"id": run_data.get("task_id")})
                    if task_response.status and task_response.data and len(task_response.data) > 0:
                        task_data = task_response.data[0]
                        task = (
                            task_data.get("config")
                            if isinstance(task_data.get("config"), EvalTask)
                            else EvalTask.model_validate(task_data.get("config"))
                        )

                return {
                    "task": task,
                    "runner_config": run_data.get("runner_config"),
                    "judge_config": run_data.get("judge_config"),
                    "criteria_configs": run_data.get("criteria_configs"),
                    "status": run_data.get("status"),
                    "run_result": run_data.get("run_result"),
                    "score_result": run_data.get("score_result"),
                    "name": run_data.get("name"),
                    "description": run_data.get("description"),
                    "created_at": run_data.get("created_at"),
                    "updated_at": run_data.get("updated_at"),
                }
        else:
            # Retrieve from memory
            return self._runs.get(run_id)

        return None
def get_plan_status(self, exclude: List[str] = None) -> str:
        # prepare components of a plan status
        exclude = exclude or []
        exclude_prompt = "omit here"
        finished_tasks = self.plan.get_finished_tasks()
        code_written = [remove_comments(task.code) for task in finished_tasks]
        code_written = "\n\n".join(code_written)
        task_results = [task.result for task in finished_tasks]
        task_results = "\n\n".join(task_results)
        task_type_name = self.current_task.task_type
        task_type = TaskType.get_type(task_type_name)
        guidance = task_type.guidance if task_type else ""

        # combine components in a prompt
        prompt = PLAN_STATUS.format(
            code_written=code_written if "code" not in exclude else exclude_prompt,
            task_results=task_results if "task_result" not in exclude else exclude_prompt,
            current_task=self.current_task.instruction,
            current_task_code=self.current_task.code if "code" not in exclude else exclude_prompt,
            current_task_result=self.current_task.result if "task_result" not in exclude else exclude_prompt,
            guidance=guidance,
        )

        return prompt
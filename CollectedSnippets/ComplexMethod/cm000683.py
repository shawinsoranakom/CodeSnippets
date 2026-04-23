async def run(
        self,
        input_data: Input,
        *,
        credentials: TodoistCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            due_date = (
                input_data.due_date.strftime("%Y-%m-%d")
                if input_data.due_date
                else None
            )
            deadline_date = (
                input_data.deadline_date.strftime("%Y-%m-%d")
                if input_data.deadline_date
                else None
            )

            task_updates = {}
            update_fields = {
                "content": input_data.content,
                "description": input_data.description,
                "project_id": input_data.project_id,
                "section_id": input_data.section_id,
                "parent_id": input_data.parent_id,
                "order": input_data.order,
                "labels": input_data.labels,
                "priority": input_data.priority,
                "due_date": due_date,
                "deadline_date": deadline_date,
                "assignee_id": input_data.assignee_id,
                "duration": input_data.duration,
                "duration_unit": input_data.duration_unit,
            }

            # Filter out None values
            task_updates = {k: v for k, v in update_fields.items() if v is not None}

            self.update_task(
                credentials,
                input_data.task_id,
                **{k: v for k, v in task_updates.items() if v is not None},
            )

            yield "success", True

        except Exception as e:
            yield "error", str(e)
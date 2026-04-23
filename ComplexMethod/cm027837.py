async def update_task(self, task_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task."""
        try:
            current_task = await self.get_task(task_id)
            if "task_type" in updates and updates["task_type"] != current_task["task_type"]:
                existing_task = await self.check_task_exists(updates["task_type"])
                if existing_task and existing_task["id"] != task_id:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A task with type '{updates['task_type']}' already exists (Task: '{existing_task['name']}', ID: {existing_task['id']}). You cannot have duplicate task types in the system.",
                    )
                if updates["task_type"] in TASK_TYPES:
                    updates["command"] = TASK_TYPES[updates["task_type"]]["command"]
            allowed_fields = [
                "name",
                "description",
                "command",
                "task_type",
                "frequency",
                "frequency_unit",
                "enabled",
            ]
            set_clauses = []
            params = []
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == "enabled":
                        value = 1 if value else 0
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            if not set_clauses:
                return await self.get_task(task_id)
            params.append(task_id)
            update_query = f"""
            UPDATE tasks
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """
            await tasks_db.execute_query(update_query, tuple(params))
            return await self.get_task(task_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")
async def get_task_executions(self, task_id: Optional[int] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get paginated task executions."""
        try:
            offset = (page - 1) * per_page
            if task_id:
                count_query = """
                SELECT COUNT(*) as count
                FROM task_executions
                WHERE task_id = ?
                """
                count_params = (task_id,)
                query = """
                SELECT id, task_id, start_time, end_time, status, error_message, output
                FROM task_executions
                WHERE task_id = ?
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
                """
                params = (task_id, per_page, offset)
            else:
                count_query = """
                SELECT COUNT(*) as count
                FROM task_executions
                """
                count_params = ()
                query = """
                SELECT id, task_id, start_time, end_time, status, error_message, output
                FROM task_executions
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
                """
                params = (per_page, offset)
            count_result = await tasks_db.execute_query(count_query, count_params, fetch=True, fetch_one=True)
            total_items = count_result.get("count", 0) if count_result else 0
            executions = await tasks_db.execute_query(query, params, fetch=True)
            for execution in executions:
                if execution.get("task_id"):
                    try:
                        task = await self.get_task(execution["task_id"])
                        execution["task_name"] = task.get("name", "Unknown Task")
                    except Exception as _:
                        execution["task_name"] = "Unknown Task"
            total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            return {
                "items": executions,
                "total": total_items,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching task executions: {str(e)}")
def update(self) -> None:
        """Get the latest data."""
        tasks = self._coordinator.data
        if self._id is None:
            project_task_data = [
                task
                for task in tasks
                if not self._project_id_whitelist
                or task.project_id in self._project_id_whitelist
            ]
        else:
            project_task_data = [task for task in tasks if task.project_id == self._id]

        # If we have no data, we can just return right away.
        if not project_task_data:
            _LOGGER.debug("No data for %s", self._name)
            self.event = None
            return

        # Keep an updated list of all tasks in this project.
        project_tasks = []
        for task in project_task_data:
            todoist_task = self.create_todoist_task(task)
            if todoist_task is not None:
                # A None task means it is invalid for this project
                project_tasks.append(todoist_task)

        if not project_tasks:
            # We had no valid tasks
            _LOGGER.debug("No valid tasks for %s", self._name)
            self.event = None
            return

        # Make sure the task collection is reset to prevent an
        # infinite collection repeating the same tasks
        self.all_project_tasks.clear()

        # Organize the best tasks (so users can see all the tasks
        # they have, organized)
        while project_tasks:
            best_task = self.select_best_task(project_tasks)
            _LOGGER.debug("Found Todoist Task: %s", best_task[SUMMARY])
            project_tasks.remove(best_task)
            self.all_project_tasks.append(best_task)

        event = self.all_project_tasks[0]
        if event is None or event[START] is None:
            _LOGGER.debug("No valid event or event start for %s", self._name)
            self.event = None
            return
        self.event = event
        _LOGGER.debug("Updated %s", self._name)
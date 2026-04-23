def get_tasks(
        self, project_gids: list[str] | None, start_date: str
    ) -> Iterator[AsanaTask]:
        """Get all tasks from the projects with the given gids that were modified since the given date.
        If project_gids is None, get all tasks from all projects in the workspace."""
        logging.info("Starting to fetch Asana projects")
        projects = self.project_api.get_projects(
            opts={
                "workspace": self.workspace_gid,
                "opt_fields": "gid,name,archived,modified_at",
            }
        )
        start_seconds = int(time.mktime(datetime.now().timetuple()))
        projects_list = []
        project_count = 0
        for project_info in projects:
            project_gid = project_info["gid"]
            if project_gids is None or project_gid in project_gids:
                projects_list.append(project_gid)
            else:
                logging.debug(
                    f"Skipping project: {project_gid} - not in accepted project_gids"
                )
            project_count += 1
            if project_count % 100 == 0:
                logging.info(f"Processed {project_count} projects")
        logging.info(f"Found {len(projects_list)} projects to process")
        for project_gid in projects_list:
            for task in self._get_tasks_for_project(
                project_gid, start_date, start_seconds
            ):
                yield task
        logging.info(f"Completed fetching {self.task_count} tasks from Asana")
        if self.api_error_count > 0:
            logging.warning(
                f"Encountered {self.api_error_count} API errors during task fetching"
            )
def _get_tasks_for_project(
        self, project_gid: str, start_date: str, start_seconds: int
    ) -> Iterator[AsanaTask]:
        project = self.project_api.get_project(project_gid, opts={})
        project_name = project.get("name", project_gid)
        team = project.get("team") or {}
        team_gid = team.get("gid")

        if project.get("archived"):
            logging.info(f"Skipping archived project: {project_name} ({project_gid})")
            return
        if not team_gid:
            logging.info(
                f"Skipping project without a team: {project_name} ({project_gid})"
            )
            return
        if project.get("privacy_setting") == "private":
            if self.team_gid and team_gid != self.team_gid:
                logging.info(
                    f"Skipping private project not in configured team: {project_name} ({project_gid})"
                )
                return
            logging.info(
                f"Processing private project in configured team: {project_name} ({project_gid})"
            )

        simple_start_date = start_date.split(".")[0].split("+")[0]
        logging.info(
            f"Fetching tasks modified since {simple_start_date} for project: {project_name} ({project_gid})"
        )

        opts = {
            "opt_fields": "name,memberships,memberships.project,completed_at,completed_by,created_at,"
            "created_by,custom_fields,dependencies,due_at,due_on,external,html_notes,liked,likes,"
            "modified_at,notes,num_hearts,parent,projects,resource_subtype,resource_type,start_on,"
            "workspace,permalink_url",
            "modified_since": start_date,
        }
        tasks_from_api = self.tasks_api.get_tasks_for_project(project_gid, opts)
        for data in tasks_from_api:
            self.task_count += 1
            if self.task_count % 10 == 0:
                end_seconds = time.mktime(datetime.now().timetuple())
                runtime_seconds = end_seconds - start_seconds
                if runtime_seconds > 0:
                    logging.info(
                        f"Processed {self.task_count} tasks in {runtime_seconds:.0f} seconds "
                        f"({self.task_count / runtime_seconds:.2f} tasks/second)"
                    )

            logging.debug(f"Processing Asana task: {data['name']}")

            text = self._construct_task_text(data)

            try:
                text += self._fetch_and_add_comments(data["gid"])

                last_modified_date = self.format_date(data["modified_at"])
                text += f"Last modified: {last_modified_date}\n"

                task = AsanaTask(
                    id=data["gid"],
                    title=data["name"],
                    text=text,
                    link=data["permalink_url"],
                    last_modified=datetime.fromisoformat(data["modified_at"]),
                    project_gid=project_gid,
                    project_name=project_name,
                )
                yield task
            except Exception:
                logging.error(
                    f"Error processing task {data['gid']} in project {project_gid}",
                    exc_info=True,
                )
                self.api_error_count += 1
async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        design_filename: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a project schedule given a project system design file.

        Args:
            user_requirement (str, optional): A string specifying the user's requirements. Defaults to an empty string.
            design_filename (str): The output file path of the document. Defaults to an empty string.
            output_pathname (str, optional): The output path name of file that the project schedule should be saved to.
            **kwargs: Additional keyword arguments.

        Returns:
            str: Path to the generated project schedule.

        Example:
            # Write a project schedule with a given system design.
            >>> design_filename = "/absolute/path/to/snake_game/docs/system_design.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/project_schedule.json"
            >>> user_requirement = "Write project schedule for a snake game following these requirements:..."
            >>> action = WriteTasks()
            >>> result = await action.run(user_requirement=user_requirement, design_filename=design_filename, output_pathname=output_pathname)
            >>> print(result)
            The project schedule is at /absolute/path/to/snake_game/docs/project_schedule.json

            # Write a project schedule with a user requirement.
            >>> user_requirement = "Write project schedule for a snake game following these requirements: ..."
            >>> output_pathname = "/absolute/path/to/snake_game/docs/project_schedule.json"
            >>> action = WriteTasks()
            >>> result = await action.run(user_requirement=user_requirement, output_pathname=output_pathname)
            >>> print(result)
            The project schedule is at /absolute/path/to/snake_game/docs/project_schedule.json
        """
        if not with_messages:
            return await self._execute_api(
                user_requirement=user_requirement, design_filename=design_filename, output_pathname=output_pathname
            )

        self.input_args = with_messages[-1].instruct_content
        self.repo = ProjectRepo(self.input_args.project_path)
        changed_system_designs = self.input_args.changed_system_design_filenames
        changed_tasks = [str(self.repo.docs.task.workdir / i) for i in list(self.repo.docs.task.changed_files.keys())]
        change_files = Documents()
        # Rewrite the system designs that have undergone changes based on the git head diff under
        # `docs/system_designs/`.
        for filename in changed_system_designs:
            task_doc = await self._update_tasks(filename=filename)
            change_files.docs[str(self.repo.docs.task.workdir / task_doc.filename)] = task_doc

        # Rewrite the task files that have undergone changes based on the git head diff under `docs/tasks/`.
        for filename in changed_tasks:
            if filename in change_files.docs:
                continue
            task_doc = await self._update_tasks(filename=filename)
            change_files.docs[filename] = task_doc

        if not change_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/tasks/` are processed before sending the publish_message, leaving room for
        # global optimization in subsequent steps.
        kvs = self.input_args.model_dump()
        kvs["changed_task_filenames"] = [
            str(self.repo.docs.task.workdir / i) for i in list(self.repo.docs.task.changed_files.keys())
        ]
        kvs["python_package_dependency_filename"] = str(self.repo.workdir / PACKAGE_REQUIREMENTS_FILENAME)
        return AIMessage(
            content="WBS is completed. "
            + "\n".join(
                [PACKAGE_REQUIREMENTS_FILENAME]
                + list(self.repo.docs.task.changed_files.keys())
                + list(self.repo.resources.api_spec_and_task.changed_files.keys())
            ),
            instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WriteTaskOutput"),
            cause_by=self,
        )
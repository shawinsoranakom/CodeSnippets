async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        prd_filename: str = "",
        legacy_design_filename: str = "",
        extra_info: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a system design.

        Args:
            user_requirement (str): The user's requirements for the system design.
            prd_filename (str, optional): The filename of the Product Requirement Document (PRD).
            legacy_design_filename (str, optional): The filename of the legacy design document.
            extra_info (str, optional): Additional information to be included in the system design.
            output_pathname (str, optional): The output file path of the document.

        Returns:
            str: The file path of the generated system design.

        Example:
            # Write a new system design and save to the path name.
            >>> user_requirement = "Write system design for a snake game"
            >>> extra_info = "Your extra information"
            >>> output_pathname = "snake_game/docs/system_design.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/system_design.json"

            # Rewrite an existing system design and save to the path name.
            >>> user_requirement = "Write system design for a snake game, include new features such as a web UI"
            >>> extra_info = "Your extra information"
            >>> legacy_design_filename = "/absolute/path/to/snake_game/docs/system_design.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/system_design_new.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, legacy_design_filename=legacy_design_filename, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/system_design_new.json"

            # Write a new system design with the given PRD(Product Requirement Document) and save to the path name.
            >>> user_requirement = "Write system design for a snake game based on the PRD at /absolute/path/to/snake_game/docs/prd.json"
            >>> extra_info = "Your extra information"
            >>> prd_filename = "/absolute/path/to/snake_game/docs/prd.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/sytem_design.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, prd_filename=prd_filename, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/sytem_design.json"

            # Rewrite an existing system design with the given PRD(Product Requirement Document) and save to the path name.
            >>> user_requirement = "Write system design for a snake game, include new features such as a web UI"
            >>> extra_info = "Your extra information"
            >>> prd_filename = "/absolute/path/to/snake_game/docs/prd.json"
            >>> legacy_design_filename = "/absolute/path/to/snake_game/docs/system_design.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/system_design_new.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, prd_filename=prd_filename, legacy_design_filename=legacy_design_filename, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/system_design_new.json"
        """
        if not with_messages:
            return await self._execute_api(
                user_requirement=user_requirement,
                prd_filename=prd_filename,
                legacy_design_filename=legacy_design_filename,
                extra_info=extra_info,
                output_pathname=output_pathname,
            )

        self.input_args = with_messages[-1].instruct_content
        self.repo = ProjectRepo(self.input_args.project_path)
        changed_prds = self.input_args.changed_prd_filenames
        changed_system_designs = [
            str(self.repo.docs.system_design.workdir / i)
            for i in list(self.repo.docs.system_design.changed_files.keys())
        ]

        # For those PRDs and design documents that have undergone changes, regenerate the design content.
        changed_files = Documents()
        for filename in changed_prds:
            doc = await self._update_system_design(filename=filename)
            changed_files.docs[filename] = doc

        for filename in changed_system_designs:
            if filename in changed_files.docs:
                continue
            doc = await self._update_system_design(filename=filename)
            changed_files.docs[filename] = doc
        if not changed_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/system_designs/` are processed before sending the publish message,
        # leaving room for global optimization in subsequent steps.
        kvs = self.input_args.model_dump()
        kvs["changed_system_design_filenames"] = [
            str(self.repo.docs.system_design.workdir / i)
            for i in list(self.repo.docs.system_design.changed_files.keys())
        ]
        return AIMessage(
            content="Designing is complete. "
            + "\n".join(
                list(self.repo.docs.system_design.changed_files.keys())
                + list(self.repo.resources.data_api_design.changed_files.keys())
                + list(self.repo.resources.seq_flow.changed_files.keys())
            ),
            instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WriteDesignOutput"),
            cause_by=self,
        )
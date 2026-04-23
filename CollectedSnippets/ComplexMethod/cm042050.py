async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        output_pathname: str = "",
        legacy_prd_filename: str = "",
        extra_info: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a Product Requirement Document.

        Args:
            user_requirement (str): A string detailing the user's requirements.
            output_pathname (str, optional): The output file path of the document. Defaults to "".
            legacy_prd_filename (str, optional): The file path of the legacy Product Requirement Document to use as a reference. Defaults to "".
            extra_info (str, optional): Additional information to include in the document. Defaults to "".
            **kwargs: Additional keyword arguments.

        Returns:
            str: The file path of the generated Product Requirement Document.

        Example:
            # Write a new PRD (Product Requirement Document)
            >>> user_requirement = "Write a snake game"
            >>> output_pathname = "snake_game/docs/prd.json"
            >>> extra_info = "YOUR EXTRA INFO, if any"
            >>> write_prd = WritePRD()
            >>> result = await write_prd.run(user_requirement=user_requirement, output_pathname=output_pathname, extra_info=extra_info)
            >>> print(result)
            PRD filename: "/absolute/path/to/snake_game/docs/prd.json"

            # Rewrite an existing PRD (Product Requirement Document) and save to a new path.
            >>> user_requirement = "Write PRD for a snake game, include new features such as a web UI"
            >>> legacy_prd_filename = "/absolute/path/to/snake_game/docs/prd.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/prd_new.json"
            >>> extra_info = "YOUR EXTRA INFO, if any"
            >>> write_prd = WritePRD()
            >>> result = await write_prd.run(user_requirement=user_requirement, legacy_prd_filename=legacy_prd_filename, extra_info=extra_info)
            >>> print(result)
            PRD filename: "/absolute/path/to/snake_game/docs/prd_new.json"
        """
        if not with_messages:
            return await self._execute_api(
                user_requirement=user_requirement,
                output_pathname=output_pathname,
                legacy_prd_filename=legacy_prd_filename,
                extra_info=extra_info,
            )

        self.input_args = with_messages[-1].instruct_content
        if not self.input_args:
            self.repo = ProjectRepo(self.context.kwargs.project_path)
            await self.repo.docs.save(filename=REQUIREMENT_FILENAME, content=with_messages[-1].content)
            self.input_args = AIMessage.create_instruct_value(
                kvs={
                    "project_path": self.context.kwargs.project_path,
                    "requirements_filename": str(self.repo.docs.workdir / REQUIREMENT_FILENAME),
                    "prd_filenames": [str(self.repo.docs.prd.workdir / i) for i in self.repo.docs.prd.all_files],
                },
                class_name="PrepareDocumentsOutput",
            )
        else:
            self.repo = ProjectRepo(self.input_args.project_path)
        req = await Document.load(filename=self.input_args.requirements_filename)
        docs: list[Document] = [
            await Document.load(filename=i, project_path=self.repo.workdir) for i in self.input_args.prd_filenames
        ]

        if not req:
            raise FileNotFoundError("No requirement document found.")

        if await self._is_bugfix(req.content):
            logger.info(f"Bugfix detected: {req.content}")
            return await self._handle_bugfix(req)
        # remove bugfix file from last round in case of conflict
        await self.repo.docs.delete(filename=BUGFIX_FILENAME)

        # if requirement is related to other documents, update them, otherwise create a new one
        if related_docs := await self.get_related_docs(req, docs):
            logger.info(f"Requirement update detected: {req.content}")
            await self._handle_requirement_update(req=req, related_docs=related_docs)
        else:
            logger.info(f"New requirement detected: {req.content}")
            await self._handle_new_requirement(req)

        kvs = self.input_args.model_dump()
        kvs["changed_prd_filenames"] = [
            str(self.repo.docs.prd.workdir / i) for i in list(self.repo.docs.prd.changed_files.keys())
        ]
        kvs["project_path"] = str(self.repo.workdir)
        kvs["requirements_filename"] = str(self.repo.docs.workdir / REQUIREMENT_FILENAME)
        self.context.kwargs.project_path = str(self.repo.workdir)
        return AIMessage(
            content="PRD is completed. "
            + "\n".join(
                list(self.repo.docs.prd.changed_files.keys())
                + list(self.repo.resources.prd.changed_files.keys())
                + list(self.repo.resources.competitive_analysis.changed_files.keys())
            ),
            instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WritePRDOutput"),
            cause_by=self,
        )
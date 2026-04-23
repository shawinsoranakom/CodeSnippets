async def _act_summarize(self):
        tasks = []
        for todo in self.summarize_todos:
            if self.n_summarize >= self.config.max_auto_summarize_code:
                break
            summary = await todo.run()
            summary_filename = Path(todo.i_context.design_filename).with_suffix(".md").name
            dependencies = {todo.i_context.design_filename, todo.i_context.task_filename}
            for filename in todo.i_context.codes_filenames:
                rpath = self.repo.src_relative_path / filename
                dependencies.add(str(rpath))
            await self.repo.resources.code_summary.save(
                filename=summary_filename, content=summary, dependencies=dependencies
            )
            is_pass, reason = await self._is_pass(summary)
            if not is_pass:
                todo.i_context.reason = reason
                tasks.append(todo.i_context.model_dump())

                await self.repo.docs.code_summary.save(
                    filename=Path(todo.i_context.design_filename).name,
                    content=todo.i_context.model_dump_json(),
                    dependencies=dependencies,
                )
            else:
                await self.repo.docs.code_summary.delete(filename=Path(todo.i_context.design_filename).name)
        self.summarize_todos = []
        logger.info(f"--max-auto-summarize-code={self.config.max_auto_summarize_code}")
        if not tasks or self.config.max_auto_summarize_code == 0:
            self.n_summarize = 0
            kvs = self.input_args.model_dump()
            kvs["changed_src_filenames"] = [
                str(self.repo.srcs.workdir / i) for i in list(self.repo.srcs.changed_files.keys())
            ]
            if self.repo.docs.code_plan_and_change.changed_files:
                kvs["changed_code_plan_and_change_filenames"] = [
                    str(self.repo.docs.code_plan_and_change.workdir / i)
                    for i in list(self.repo.docs.code_plan_and_change.changed_files.keys())
                ]
            if self.repo.docs.code_summary.changed_files:
                kvs["changed_code_summary_filenames"] = [
                    str(self.repo.docs.code_summary.workdir / i)
                    for i in list(self.repo.docs.code_summary.changed_files.keys())
                ]
            return AIMessage(
                content=f"Coding is complete. The source code is at {self.repo.workdir.name}/{self.repo.srcs.root_path}, containing: "
                + "\n".join(
                    list(self.repo.resources.code_summary.changed_files.keys())
                    + list(self.repo.srcs.changed_files.keys())
                    + list(self.repo.resources.code_plan_and_change.changed_files.keys())
                ),
                instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="SummarizeCodeOutput"),
                cause_by=SummarizeCode,
                send_to="Edward",  # The name of QaEngineer
            )
        # The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating unlimited.
        # This parameter is used for debugging the workflow.
        self.n_summarize += 1 if self.config.max_auto_summarize_code > self.n_summarize else 0
        return AIMessage(content="", cause_by=SummarizeCode, send_to=MESSAGE_ROUTE_TO_SELF)
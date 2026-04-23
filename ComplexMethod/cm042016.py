async def _new_code_actions(self):
        bug_fix = await self._is_fixbug()
        # Prepare file repos
        changed_src_files = self.repo.srcs.changed_files
        if self.context.kwargs.src_filename:
            changed_src_files = {self.context.kwargs.src_filename: ChangeType.UNTRACTED}
        if bug_fix:
            changed_src_files = self.repo.srcs.all_files
        changed_files = Documents()
        # Recode caused by upstream changes.
        if hasattr(self.input_args, "changed_task_filenames"):
            changed_task_filenames = self.input_args.changed_task_filenames
        else:
            changed_task_filenames = [
                str(self.repo.docs.task.workdir / i) for i in list(self.repo.docs.task.changed_files.keys())
            ]
        for filename in changed_task_filenames:
            task_filename = Path(filename)
            design_filename = None
            if hasattr(self.input_args, "changed_system_design_filenames"):
                changed_system_design_filenames = self.input_args.changed_system_design_filenames
            else:
                changed_system_design_filenames = [
                    str(self.repo.docs.system_design.workdir / i)
                    for i in list(self.repo.docs.system_design.changed_files.keys())
                ]
            for i in changed_system_design_filenames:
                if task_filename.name == Path(i).name:
                    design_filename = Path(i)
                    break
            code_plan_and_change_filename = None
            if hasattr(self.input_args, "changed_code_plan_and_change_filenames"):
                changed_code_plan_and_change_filenames = self.input_args.changed_code_plan_and_change_filenames
            else:
                changed_code_plan_and_change_filenames = [
                    str(self.repo.docs.code_plan_and_change.workdir / i)
                    for i in list(self.repo.docs.code_plan_and_change.changed_files.keys())
                ]
            for i in changed_code_plan_and_change_filenames:
                if task_filename.name == Path(i).name:
                    code_plan_and_change_filename = Path(i)
                    break
            design_doc = await Document.load(filename=design_filename, project_path=self.repo.workdir)
            task_doc = await Document.load(filename=task_filename, project_path=self.repo.workdir)
            code_plan_and_change_doc = await Document.load(
                filename=code_plan_and_change_filename, project_path=self.repo.workdir
            )
            task_list = self._parse_tasks(task_doc)
            await self._init_python_folder(task_list)
            for task_filename in task_list:
                if self.context.kwargs.src_filename and task_filename != self.context.kwargs.src_filename:
                    continue
                old_code_doc = await self.repo.srcs.get(task_filename)
                if not old_code_doc:
                    old_code_doc = Document(
                        root_path=str(self.repo.src_relative_path), filename=task_filename, content=""
                    )
                if not code_plan_and_change_doc:
                    context = CodingContext(
                        filename=task_filename, design_doc=design_doc, task_doc=task_doc, code_doc=old_code_doc
                    )
                else:
                    context = CodingContext(
                        filename=task_filename,
                        design_doc=design_doc,
                        task_doc=task_doc,
                        code_doc=old_code_doc,
                        code_plan_and_change_doc=code_plan_and_change_doc,
                    )
                coding_doc = Document(
                    root_path=str(self.repo.src_relative_path),
                    filename=task_filename,
                    content=context.model_dump_json(),
                )
                if task_filename in changed_files.docs:
                    logger.warning(
                        f"Log to expose potential conflicts: {coding_doc.model_dump_json()} & "
                        f"{changed_files.docs[task_filename].model_dump_json()}"
                    )
                changed_files.docs[task_filename] = coding_doc
        self.code_todos = [
            WriteCode(i_context=i, repo=self.repo, input_args=self.input_args, context=self.context, llm=self.llm)
            for i in changed_files.docs.values()
        ]
        # Code directly modified by the user.
        dependency = await self.repo.git_repo.get_dependency()
        for filename in changed_src_files:
            if filename in changed_files.docs:
                continue
            coding_doc = await self._new_coding_doc(filename=filename, dependency=dependency)
            if not coding_doc:
                continue  # `__init__.py` created by `init_python_folder`
            changed_files.docs[filename] = coding_doc
            self.code_todos.append(
                WriteCode(
                    i_context=coding_doc, repo=self.repo, input_args=self.input_args, context=self.context, llm=self.llm
                )
            )

        if self.code_todos:
            self.set_todo(self.code_todos[0])
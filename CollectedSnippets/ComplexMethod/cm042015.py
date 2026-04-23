async def _new_coding_context(self, filename, dependency) -> Optional[CodingContext]:
        old_code_doc = await self.repo.srcs.get(filename)
        if not old_code_doc:
            old_code_doc = Document(root_path=str(self.repo.src_relative_path), filename=filename, content="")
        dependencies = {Path(i) for i in await dependency.get(old_code_doc.root_relative_path)}
        task_doc = None
        design_doc = None
        code_plan_and_change_doc = await self._get_any_code_plan_and_change() if await self._is_fixbug() else None
        for i in dependencies:
            if str(i.parent) == TASK_FILE_REPO:
                task_doc = await self.repo.docs.task.get(i.name)
            elif str(i.parent) == SYSTEM_DESIGN_FILE_REPO:
                design_doc = await self.repo.docs.system_design.get(i.name)
            elif str(i.parent) == CODE_PLAN_AND_CHANGE_FILE_REPO:
                code_plan_and_change_doc = await self.repo.docs.code_plan_and_change.get(i.name)
        if not task_doc or not design_doc:
            if filename == "__init__.py":  # `__init__.py` created by `init_python_folder`
                return None
            logger.error(f'Detected source code "{filename}" from an unknown origin.')
            raise ValueError(f'Detected source code "{filename}" from an unknown origin.')
        context = CodingContext(
            filename=filename,
            design_doc=design_doc,
            task_doc=task_doc,
            code_doc=old_code_doc,
            code_plan_and_change_doc=code_plan_and_change_doc,
        )
        return context
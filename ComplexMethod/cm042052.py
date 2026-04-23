async def run(self, *args, **kwargs) -> CodingContext:
        bug_feedback = None
        if self.input_args and hasattr(self.input_args, "issue_filename"):
            bug_feedback = await Document.load(self.input_args.issue_filename)
        coding_context = CodingContext.loads(self.i_context.content)
        if not coding_context.code_plan_and_change_doc:
            coding_context.code_plan_and_change_doc = await self.repo.docs.code_plan_and_change.get(
                filename=coding_context.task_doc.filename
            )
        test_doc = await self.repo.test_outputs.get(filename="test_" + coding_context.filename + ".json")
        requirement_doc = await Document.load(self.input_args.requirements_filename)
        summary_doc = None
        if coding_context.design_doc and coding_context.design_doc.filename:
            summary_doc = await self.repo.docs.code_summary.get(filename=coding_context.design_doc.filename)
        logs = ""
        if test_doc:
            test_detail = RunCodeResult.loads(test_doc.content)
            logs = test_detail.stderr

        if self.config.inc or bug_feedback:
            code_context = await self.get_codes(
                coding_context.task_doc, exclude=self.i_context.filename, project_repo=self.repo, use_inc=True
            )
        else:
            code_context = await self.get_codes(
                coding_context.task_doc, exclude=self.i_context.filename, project_repo=self.repo
            )

        if self.config.inc:
            prompt = REFINED_TEMPLATE.format(
                user_requirement=requirement_doc.content if requirement_doc else "",
                code_plan_and_change=coding_context.code_plan_and_change_doc.content
                if coding_context.code_plan_and_change_doc
                else "",
                design=coding_context.design_doc.content if coding_context.design_doc else "",
                task=coding_context.task_doc.content if coding_context.task_doc else "",
                code=code_context,
                logs=logs,
                feedback=bug_feedback.content if bug_feedback else "",
                filename=self.i_context.filename,
                demo_filename=Path(self.i_context.filename).stem,
                summary_log=summary_doc.content if summary_doc else "",
            )
        else:
            prompt = PROMPT_TEMPLATE.format(
                design=coding_context.design_doc.content if coding_context.design_doc else "",
                task=coding_context.task_doc.content if coding_context.task_doc else "",
                code=code_context,
                logs=logs,
                feedback=bug_feedback.content if bug_feedback else "",
                filename=self.i_context.filename,
                demo_filename=Path(self.i_context.filename).stem,
                summary_log=summary_doc.content if summary_doc else "",
            )
        logger.info(f"Writing {coding_context.filename}..")
        async with EditorReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "code", "filename": coding_context.filename}, "meta")
            code = await self.write_code(prompt)
            if not coding_context.code_doc:
                # avoid root_path pydantic ValidationError if use WriteCode alone
                coding_context.code_doc = Document(
                    filename=coding_context.filename, root_path=str(self.repo.src_relative_path)
                )
            coding_context.code_doc.content = code
            await reporter.async_report(coding_context.code_doc, "document")
        return coding_context
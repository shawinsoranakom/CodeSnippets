async def _write_test(self, message: Message) -> None:
        reqa_file = self.context.kwargs.reqa_file or self.config.reqa_file
        changed_files = {reqa_file} if reqa_file else set(self.repo.srcs.changed_files.keys())
        for filename in changed_files:
            # write tests
            if not filename or "test" in filename:
                continue
            code_doc = await self.repo.srcs.get(filename)
            if not code_doc or not code_doc.content:
                continue
            if not code_doc.filename.endswith(".py"):
                continue
            test_doc = await self.repo.tests.get("test_" + code_doc.filename)
            if not test_doc:
                test_doc = Document(
                    root_path=str(self.repo.tests.root_path), filename="test_" + code_doc.filename, content=""
                )
            logger.info(f"Writing {test_doc.filename}..")
            context = TestingContext(filename=test_doc.filename, test_doc=test_doc, code_doc=code_doc)

            context = await WriteTest(i_context=context, context=self.context, llm=self.llm).run()
            async with EditorReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report({"type": "test", "filename": test_doc.filename}, "meta")

                doc = await self.repo.tests.save_doc(
                    doc=context.test_doc, dependencies={context.code_doc.root_relative_path}
                )
                await reporter.async_report(self.repo.workdir / doc.root_relative_path, "path")

            # prepare context for run tests in next round
            run_code_context = RunCodeContext(
                command=["python", context.test_doc.root_relative_path],
                code_filename=context.code_doc.filename,
                test_filename=context.test_doc.filename,
                working_directory=str(self.repo.workdir),
                additional_python_paths=[str(self.repo.srcs.workdir)],
            )
            self.publish_message(
                AIMessage(content=run_code_context.model_dump_json(), cause_by=WriteTest, send_to=MESSAGE_ROUTE_TO_SELF)
            )

        logger.info(f"Done {str(self.repo.tests.workdir)} generating.")
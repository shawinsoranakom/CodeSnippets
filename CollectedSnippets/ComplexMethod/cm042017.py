async def _new_summarize_actions(self):
        src_files = self.repo.srcs.all_files
        # Generate a SummarizeCode action for each pair of (system_design_doc, task_doc).
        summarizations = defaultdict(list)
        for filename in src_files:
            dependencies = await self.repo.srcs.get_dependency(filename=filename)
            ctx = CodeSummarizeContext.loads(filenames=list(dependencies))
            summarizations[ctx].append(filename)
        for ctx, filenames in summarizations.items():
            if not ctx.design_filename or not ctx.task_filename:
                continue  # cause by `__init__.py` which is created by `init_python_folder`
            ctx.codes_filenames = filenames
            new_summarize = SummarizeCode(
                i_context=ctx, repo=self.repo, input_args=self.input_args, context=self.context, llm=self.llm
            )
            for i, act in enumerate(self.summarize_todos):
                if act.i_context.task_filename == new_summarize.i_context.task_filename:
                    self.summarize_todos[i] = new_summarize
                    new_summarize = None
                    break
            if new_summarize:
                self.summarize_todos.append(new_summarize)
        if self.summarize_todos:
            self.set_todo(self.summarize_todos[0])
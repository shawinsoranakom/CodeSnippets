async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        run_id: UUID | None = None,
        **kwargs: Any,
    ) -> list[AsyncCallbackManagerForLLMRun]:
        """Run when LLM starts running.

        Args:
            serialized: The serialized LLM.
            prompts: The list of prompts.
            run_id: The ID of the run.
            **kwargs: Additional keyword arguments.

        Returns:
            The list of async callback managers, one for each LLM run corresponding to
            each prompt.
        """
        inline_tasks = []
        non_inline_tasks = []
        inline_handlers = [handler for handler in self.handlers if handler.run_inline]
        non_inline_handlers = [
            handler for handler in self.handlers if not handler.run_inline
        ]
        managers = []

        for prompt in prompts:
            if run_id is not None:
                run_id_ = run_id
                run_id = None
            else:
                run_id_ = uuid7()

            if inline_handlers:
                inline_tasks.append(
                    ahandle_event(
                        inline_handlers,
                        "on_llm_start",
                        "ignore_llm",
                        serialized,
                        [prompt],
                        run_id=run_id_,
                        parent_run_id=self.parent_run_id,
                        tags=self.tags,
                        metadata=self.metadata,
                        **kwargs,
                    )
                )
            else:
                non_inline_tasks.append(
                    ahandle_event(
                        non_inline_handlers,
                        "on_llm_start",
                        "ignore_llm",
                        serialized,
                        [prompt],
                        run_id=run_id_,
                        parent_run_id=self.parent_run_id,
                        tags=self.tags,
                        metadata=self.metadata,
                        **kwargs,
                    )
                )

            managers.append(
                AsyncCallbackManagerForLLMRun(
                    run_id=run_id_,
                    handlers=self.handlers,
                    inheritable_handlers=self.inheritable_handlers,
                    parent_run_id=self.parent_run_id,
                    tags=self.tags,
                    inheritable_tags=self.inheritable_tags,
                    metadata=self.metadata,
                    inheritable_metadata=self.inheritable_metadata,
                )
            )

        # Run inline tasks sequentially
        for inline_task in inline_tasks:
            await inline_task

        # Run non-inline tasks concurrently
        if non_inline_tasks:
            await asyncio.gather(*non_inline_tasks)

        return managers
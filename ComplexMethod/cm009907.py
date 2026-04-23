async def _acall(
        self,
        inputs: dict[str, Any],
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> dict[str, Any]:
        _run_manager = run_manager or AsyncCallbackManagerForChainRun.get_noop_manager()
        question = inputs["question"]
        get_chat_history = self.get_chat_history or _get_chat_history
        chat_history_str = get_chat_history(inputs["chat_history"])
        if chat_history_str:
            callbacks = _run_manager.get_child()
            new_question = await self.question_generator.arun(
                question=question,
                chat_history=chat_history_str,
                callbacks=callbacks,
            )
        else:
            new_question = question
        accepts_run_manager = (
            "run_manager" in inspect.signature(self._aget_docs).parameters
        )
        if accepts_run_manager:
            docs = await self._aget_docs(new_question, inputs, run_manager=_run_manager)
        else:
            docs = await self._aget_docs(new_question, inputs)  # type: ignore[call-arg]

        output: dict[str, Any] = {}
        if self.response_if_no_docs_found is not None and len(docs) == 0:
            output[self.output_key] = self.response_if_no_docs_found
        else:
            new_inputs = inputs.copy()
            if self.rephrase_question:
                new_inputs["question"] = new_question
            new_inputs["chat_history"] = chat_history_str
            answer = await self.combine_docs_chain.arun(
                input_documents=docs,
                callbacks=_run_manager.get_child(),
                **new_inputs,
            )
            output[self.output_key] = answer

        if self.return_source_documents:
            output["source_documents"] = docs
        if self.return_generated_question:
            output["generated_question"] = new_question
        return output
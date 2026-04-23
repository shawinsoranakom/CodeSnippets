async def _resolve_candidate(self, candidate_resolution_i: tuple[str, list[tuple[str, str]]], resolution_result: set[str], resolution_result_lock: asyncio.Lock, task_id: str = ""):
        if task_id:
            if has_canceled(task_id):
                logging.info(f"Task {task_id} cancelled during entity resolution candidate processing.")
                raise TaskCanceledException(f"Task {task_id} was cancelled")

        pair_txt = [
            f'When determining whether two {candidate_resolution_i[0]}s are the same, you should only focus on critical properties and overlook noisy factors.\n']
        for index, candidate in enumerate(candidate_resolution_i[1]):
            pair_txt.append(
                f'Question {index + 1}: name of{candidate_resolution_i[0]} A is {candidate[0]} ,name of{candidate_resolution_i[0]} B is {candidate[1]}')
        sent = 'question above' if len(pair_txt) == 1 else f'above {len(pair_txt)} questions'
        pair_txt.append(
            f'\nUse domain knowledge of {candidate_resolution_i[0]}s to help understand the text and answer the {sent} in the format: For Question i, Yes, {candidate_resolution_i[0]} A and {candidate_resolution_i[0]} B are the same {candidate_resolution_i[0]}./No, {candidate_resolution_i[0]} A and {candidate_resolution_i[0]} B are different {candidate_resolution_i[0]}s. For Question i+1, (repeat the above procedures)')
        pair_prompt = '\n'.join(pair_txt)
        variables = {
            **self.prompt_variables,
            self._input_text_key: pair_prompt
        }
        text = perform_variable_replacements(self._resolution_prompt, variables=variables)
        logging.info(f"Created resolution prompt {len(text)} bytes for {len(candidate_resolution_i[1])} entity pairs of type {candidate_resolution_i[0]}")
        async with chat_limiter:
            timeout_seconds = 280 if os.environ.get("ENABLE_TIMEOUT_ASSERTION") else 1000000000
            try:
                response = await asyncio.wait_for(
                    self._async_chat(text, [{"role": "user", "content": "Output:"}], {}, task_id),
                    timeout=timeout_seconds,
                )

            except asyncio.TimeoutError:
                logging.warning("_resolve_candidate._async_chat timeout, skipping...")
                return
            except Exception as e:
                logging.error(f"_resolve_candidate._async_chat failed: {e}")
                return

        logging.debug(f"_resolve_candidate chat prompt: {text}\nchat response: {response}")
        result = self._process_results(len(candidate_resolution_i[1]), response,
                                       self.prompt_variables.get(self._record_delimiter_key,
                                                            DEFAULT_RECORD_DELIMITER),
                                       self.prompt_variables.get(self._entity_index_delimiter_key,
                                                            DEFAULT_ENTITY_INDEX_DELIMITER),
                                       self.prompt_variables.get(self._resolution_result_delimiter_key,
                                                            DEFAULT_RESOLUTION_RESULT_DELIMITER))
        async with resolution_result_lock:
            for result_i in result:
                resolution_result.add(candidate_resolution_i[1][result_i[0] - 1])
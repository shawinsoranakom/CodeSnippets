async def _async_chat(self, system, history, gen_conf={}, task_id=""):
        hist = deepcopy(history)
        conf = deepcopy(gen_conf)
        response = await thread_pool_exec(get_llm_cache, self._llm.llm_name, system, hist, conf)
        response = self._normalize_response_text(response)
        if self._is_truncated_cache(response):
            response = ""
        if response:
            return response
        _, system_msg = message_fit_in([{"role": "system", "content": system}], int(self._llm.max_length * 0.92))
        response = ""
        for attempt in range(3):
            if task_id:
                if await thread_pool_exec(has_canceled, task_id):
                    logging.info(f"Task {task_id} cancelled during entity resolution candidate processing.")
                    raise TaskCanceledException(f"Task {task_id} was cancelled")
            try:
                response = await asyncio.wait_for(
                    self._llm.async_chat(system_msg[0]["content"], hist, conf),
                    timeout=60 * 20,
                )
                response = self._normalize_response_text(response)
                response = re.sub(r"^.*</think>", "", response, flags=re.DOTALL)
                if response.find("**ERROR**") >= 0:
                    raise Exception(response)
                if not self._is_truncated_cache(response):
                    await thread_pool_exec(set_llm_cache, self._llm.llm_name, system, response, history, gen_conf)
                break
            except asyncio.TimeoutError:
                logging.warning("_async_chat timed out after 20 minutes")
                raise  # timeout is not a transient error; do not retry
            except Exception as e:
                logging.exception(e)
                if attempt == 2:
                    raise

        return response
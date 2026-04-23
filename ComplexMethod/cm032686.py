async def _process_single_content(self, chunk_key_dp: tuple[str, str], chunk_seq: int, num_chunks: int, out_results, task_id=""):
        token_count = 0
        chunk_key = chunk_key_dp[0]
        content = chunk_key_dp[1]
        variables = {
            **self._prompt_variables,
            self._input_text_key: content,
        }
        hint_prompt = perform_variable_replacements(self._extraction_prompt, variables=variables)
        async with chat_limiter:
            response = await self._async_chat(hint_prompt, [{"role": "user", "content": "Output:"}], {}, task_id)
        token_count += num_tokens_from_string(hint_prompt + response)

        results = response or ""
        history = [{"role": "system", "content": hint_prompt}, {"role": "user", "content": response}]

        # Repeat to ensure we maximize entity count
        for i in range(self._max_gleanings):
            history.append({"role": "user", "content": CONTINUE_PROMPT})
            async with chat_limiter:
                response = await self._async_chat("", history, {}, task_id)
            token_count += num_tokens_from_string("\n".join([m["content"] for m in history]) + response)
            results += response or ""

            # if this is the final glean, don't bother updating the continuation flag
            if i >= self._max_gleanings - 1:
                break
            history.append({"role": "assistant", "content": response})
            history.append({"role": "user", "content": LOOP_PROMPT})
            async with chat_limiter:
                continuation = await self._async_chat("", history, {}, task_id)
            token_count += num_tokens_from_string("\n".join([m["content"] for m in history]) + response)
            if continuation != "Y":
                break
            history.append({"role": "assistant", "content": "Y"})

        records = split_string_by_multi_markers(
            results,
            [self._prompt_variables[self._record_delimiter_key], self._prompt_variables[self._completion_delimiter_key]],
        )
        rcds = []
        for record in records:
            record = re.search(r"\((.*)\)", record)
            if record is None:
                continue
            rcds.append(record.group(1))
        records = rcds
        maybe_nodes, maybe_edges = self._entities_and_relations(chunk_key, records, self._prompt_variables[self._tuple_delimiter_key])
        out_results.append((maybe_nodes, maybe_edges, token_count))
        if self.callback:
            self.callback(0.5+0.1*len(out_results)/num_chunks, msg = f"Entities extraction of chunk {chunk_seq} {len(out_results)}/{num_chunks} done, {len(maybe_nodes)} nodes, {len(maybe_edges)} edges, {token_count} tokens.")
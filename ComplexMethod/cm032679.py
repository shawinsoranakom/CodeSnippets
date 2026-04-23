async def _process_single_content(self, chunk_key_dp: tuple[str, str], chunk_seq: int, num_chunks: int, out_results, task_id=""):
        token_count = 0
        chunk_key = chunk_key_dp[0]
        content = chunk_key_dp[1]
        hint_prompt = self._entity_extract_prompt.format(**self._context_base, input_text=content)

        gen_conf = {}
        logging.info(f"Start processing for {chunk_key}: {content[:25]}...")
        if self.callback:
            self.callback(msg=f"Start processing for {chunk_key}: {content[:25]}...")
        async with chat_limiter:
            final_result = await self._async_chat("", [{"role": "user", "content": hint_prompt}], gen_conf, task_id)
        token_count += num_tokens_from_string(hint_prompt + final_result)
        history = pack_user_ass_to_openai_messages(hint_prompt, final_result, self._continue_prompt)
        for now_glean_index in range(self._max_gleanings):
            async with chat_limiter:
                glean_result = await self._async_chat("", history, gen_conf, task_id)
            history.extend([{"role": "assistant", "content": glean_result}])
            token_count += num_tokens_from_string("\n".join([m["content"] for m in history]) + hint_prompt + self._continue_prompt)
            final_result += glean_result
            if now_glean_index == self._max_gleanings - 1:
                break

            history.extend([{"role": "user", "content": self._if_loop_prompt}])
            async with chat_limiter:
                if_loop_result = await self._async_chat("", history, gen_conf, task_id)
            token_count += num_tokens_from_string("\n".join([m["content"] for m in history]) + if_loop_result + self._if_loop_prompt)
            if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
            if if_loop_result != "yes":
                break
            history.extend([{"role": "assistant", "content": if_loop_result}, {"role": "user", "content": self._continue_prompt}])

        logging.info(f"Completed processing for {chunk_key}: {content[:25]}... after {now_glean_index} gleanings, {token_count} tokens.")
        if self.callback:
            self.callback(msg=f"Completed processing for {chunk_key}: {content[:25]}... after {now_glean_index} gleanings, {token_count} tokens.")
        records = split_string_by_multi_markers(
            final_result,
            [self._context_base["record_delimiter"], self._context_base["completion_delimiter"]],
        )
        rcds = []
        for record in records:
            record = re.search(r"\((.*)\)", record)
            if record is None:
                continue
            rcds.append(record.group(1))
        records = rcds
        maybe_nodes, maybe_edges = self._entities_and_relations(chunk_key, records, self._context_base["tuple_delimiter"])
        out_results.append((maybe_nodes, maybe_edges, token_count))
        if self.callback:
            self.callback(
                0.5 + 0.1 * len(out_results) / num_chunks,
                msg=f"Entities extraction of chunk {chunk_seq} {len(out_results)}/{num_chunks} done, {len(maybe_nodes)} nodes, {len(maybe_edges)} edges, {token_count} tokens.",
            )
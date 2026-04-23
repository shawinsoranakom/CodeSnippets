async def _batch_decode_loop(self, queue: asyncio.Queue):
        """Batch incoming decode requests for efficiency."""
        while True:
            token_ids, result_future = await queue.get()
            token_ids_list = [token_ids]
            result_futures = [result_future]
            deadline = self._loop.time() + self.batch_wait_timeout_s

            while len(token_ids_list) < self.max_batch_size:
                timeout = deadline - self._loop.time()
                if timeout <= 0:
                    break
                try:
                    token_ids, result_future = await asyncio.wait_for(
                        queue.get(), timeout
                    )
                    token_ids_list.append(token_ids)
                    result_futures.append(result_future)
                except asyncio.TimeoutError:
                    break

            try:
                # Perform a single batched decode call for all requests
                results = await self._loop.run_in_executor(
                    self._executor, self.tokenizer.batch_decode, token_ids_list
                )
                for fut, res in zip(result_futures, results):
                    if not fut.done():
                        fut.set_result(res)
            except Exception as e:
                for fut in result_futures:
                    if not fut.done():
                        fut.set_exception(e)
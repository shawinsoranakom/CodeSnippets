async def _batch_encode_loop(self, queue: asyncio.Queue, can_batch: bool):
        """Batch incoming encode requests for efficiency."""
        while True:
            prompt, kwargs, result_future = await queue.get()
            prompts = [prompt]
            kwargs_list = [kwargs]
            result_futures = [result_future]
            deadline = self._loop.time() + self.batch_wait_timeout_s

            while len(prompts) < self.max_batch_size:
                timeout = deadline - self._loop.time()
                if timeout <= 0:
                    break
                try:
                    prompt, kwargs, result_future = await asyncio.wait_for(
                        queue.get(), timeout
                    )
                    prompts.append(prompt)
                    result_futures.append(result_future)
                    if not can_batch:
                        kwargs_list.append(kwargs)
                except asyncio.TimeoutError:
                    break

            try:
                # If every request uses identical kwargs we can run a single
                # batched tokenizer call for a big speed-up.
                if can_batch and len(prompts) > 1:
                    batch_encode_fn = partial(self.tokenizer, prompts, **kwargs)
                    results = await self._loop.run_in_executor(
                        self._executor, batch_encode_fn
                    )

                    for i, fut in enumerate(result_futures):
                        if not fut.done():
                            data = {k: v[i] for k, v in results.items()}
                            fut.set_result(BatchEncoding(data))
                else:
                    encode_fn = lambda prompts=prompts, kwargs=kwargs_list: [
                        self.tokenizer(p, **kw) for p, kw in zip(prompts, kwargs)
                    ]
                    results = await self._loop.run_in_executor(
                        self._executor, encode_fn
                    )

                    for fut, res in zip(result_futures, results):
                        if not fut.done():
                            fut.set_result(res)
            except Exception as e:
                for fut in result_futures:
                    if not fut.done():
                        fut.set_exception(e)
async def worker(res_list: List[Dict[str, Any]]):
            while True:
                if queue.empty() and producer_done.is_set():
                    # self._log("debug", "Worker exiting: queue empty and producer done.", tag="URL_SEED")
                    break
                try:
                    # Increased timeout slightly
                    url = await asyncio.wait_for(queue.get(), 5)
                except asyncio.TimeoutError:
                    continue  # Keep checking queue and producer_done status
                except Exception as e:
                    self._log("error", "Worker failed to get URL from queue: {error}", params={
                              "error": str(e)}, tag="URL_SEED")
                    continue

                if max_urls > 0 and len(res_list) >= max_urls:
                    self._log(
                        "info",
                        "Worker stopping due to max_urls limit.",
                        tag="URL_SEED",
                    )
                    stop_event.set()

                    # mark the current item done
                    queue.task_done()

                    # flush whatever is still sitting in the queue so
                    # queue.join() can finish cleanly
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                            queue.task_done()
                        except asyncio.QueueEmpty:
                            break
                    break

                if self._rate_sem:  # global QPS control
                    async with self._rate_sem:
                        await self._validate(url, res_list, live_check, extract_head,
                                             head_timeout, verbose, query, score_threshold, scoring_method,
                                             filter_nonsense)
                else:
                    await self._validate(url, res_list, live_check, extract_head,
                                         head_timeout, verbose, query, score_threshold, scoring_method,
                                         filter_nonsense)
                queue.task_done()
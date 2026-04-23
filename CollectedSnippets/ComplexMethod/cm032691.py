async def __call__(self, doc_id: str, chunks: list[str], callback: Callable | None = None, task_id: str = ""):
        self.callback = callback
        start_ts = asyncio.get_running_loop().time()

        async def extract_all(doc_id, chunks, max_concurrency=MAX_CONCURRENT_PROCESS_AND_EXTRACT_CHUNK, task_id=""):
            out_results = []
            error_count = 0
            max_errors = int(os.environ.get("GRAPHRAG_MAX_ERRORS", 3))

            limiter = asyncio.Semaphore(max_concurrency)

            async def worker(chunk_key_dp: tuple[str, str], idx: int, total: int, task_id=""):
                nonlocal error_count
                async with limiter:

                    if task_id and has_canceled(task_id):
                        raise TaskCanceledException(f"Task {task_id} was cancelled during entity extraction")

                    try:
                        await self._process_single_content(chunk_key_dp, idx, total, out_results, task_id)
                    except Exception as e:
                        error_count += 1
                        error_msg = f"Error processing chunk {idx + 1}/{total}: {str(e)}"
                        logging.warning(error_msg)
                        if self.callback:
                            self.callback(msg=error_msg)

                        if error_count > max_errors:
                            raise Exception(f"Maximum error count ({max_errors}) reached. Last errors: {str(e)}")

            tasks = [
                asyncio.create_task(worker((doc_id, ck), i, len(chunks), task_id))
                for i, ck in enumerate(chunks)
            ]

            try:
                await asyncio.gather(*tasks, return_exceptions=False)
            except Exception as e:
                logging.error(f"Error in worker: {str(e)}")
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise

            if error_count > 0:
                warning_msg = f"Completed with {error_count} errors (out of {len(chunks)} chunks processed)"
                logging.warning(warning_msg)
                if self.callback:
                    self.callback(msg=warning_msg)

            return out_results

        if task_id and has_canceled(task_id):
            raise TaskCanceledException(f"Task {task_id} was cancelled before entity extraction")

        out_results = await extract_all(doc_id, chunks, max_concurrency=MAX_CONCURRENT_PROCESS_AND_EXTRACT_CHUNK, task_id=task_id)

        if task_id and has_canceled(task_id):
            raise TaskCanceledException(f"Task {task_id} was cancelled after entity extraction")

        maybe_nodes = defaultdict(list)
        maybe_edges = defaultdict(list)
        sum_token_count = 0
        for m_nodes, m_edges, token_count in out_results:
            for k, v in m_nodes.items():
                maybe_nodes[k].extend(v)
            for k, v in m_edges.items():
                maybe_edges[tuple(sorted(k))].extend(v)
            sum_token_count += token_count
        now = asyncio.get_running_loop().time()
        if self.callback:
            self.callback(msg=f"Entities and relationships extraction done, {len(maybe_nodes)} nodes, {len(maybe_edges)} edges, {sum_token_count} tokens, {now - start_ts:.2f}s.")
        start_ts = now
        logging.info("Entities merging...")
        all_entities_data = []

        if task_id and has_canceled(task_id):
            raise TaskCanceledException(f"Task {task_id} was cancelled before nodes merging")

        tasks = [
            asyncio.create_task(self._merge_nodes(en_nm, ents, all_entities_data, task_id))
            for en_nm, ents in maybe_nodes.items()
        ]
        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception as e:
            logging.error(f"Error merging nodes: {e}")
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        if task_id and has_canceled(task_id):
            raise TaskCanceledException(f"Task {task_id} was cancelled after nodes merging")

        now = asyncio.get_running_loop().time()
        if self.callback:
            self.callback(msg=f"Entities merging done, {now - start_ts:.2f}s.")

        start_ts = now
        logging.info("Relationships merging...")
        all_relationships_data = []

        if task_id and has_canceled(task_id):
            raise TaskCanceledException(f"Task {task_id} was cancelled before relationships merging")

        tasks = []
        for (src, tgt), rels in maybe_edges.items():
            tasks.append(
                asyncio.create_task(
                    self._merge_edges(src, tgt, rels, all_relationships_data, task_id)
                )
            )
        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception as e:
            logging.error(f"Error during relationships merging: {e}")
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        if task_id and has_canceled(task_id):
            raise TaskCanceledException(f"Task {task_id} was cancelled after relationships merging")

        now = asyncio.get_running_loop().time()
        if self.callback:
            self.callback(msg=f"Relationships merging done, {now - start_ts:.2f}s.")

        if not len(all_entities_data) and not len(all_relationships_data):
            logging.warning("Didn't extract any entities and relationships, maybe your LLM is not working")

        if not len(all_entities_data):
            logging.warning("Didn't extract any entities")
        if not len(all_relationships_data):
            logging.warning("Didn't extract any relationships")

        return all_entities_data, all_relationships_data
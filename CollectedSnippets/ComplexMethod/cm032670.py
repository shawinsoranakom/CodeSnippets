async def __call__(self, chunks, random_state, callback=None, task_id: str = ""):
        if len(chunks) <= 1:
            return []
        chunks = [(s, a) for s, a in chunks if s and a is not None and len(a) > 0]
        layers = [(0, len(chunks))]
        start, end = 0, len(chunks)

        @timeout(60 * 20)
        async def summarize(ck_idx: list[int]):
            nonlocal chunks

            self._check_task_canceled(task_id, "summarization")

            texts = [chunks[i][0] for i in ck_idx]
            len_per_chunk = int((self._llm_model.max_length - self._max_token) / len(texts))
            cluster_content = "\n".join([truncate(t, max(1, len_per_chunk)) for t in texts])
            try:
                async with chat_limiter:
                    self._check_task_canceled(task_id, "before LLM call")

                    cnt = await self._chat(
                        "You're a helpful assistant.",
                        [
                            {
                                "role": "user",
                                "content": self._prompt.format(cluster_content=cluster_content),
                            }
                        ],
                        {"max_tokens": max(self._max_token, 512)},  # fix issue:  #10235
                    )
                    cnt = re.sub(
                        "(······\n由于长度的原因，回答被截断了，要继续吗？|For the content length reason, it stopped, continue?)",
                        "",
                        cnt,
                    )
                    logging.debug(f"SUM: {cnt}")

                    self._check_task_canceled(task_id, "before embedding")

                    embds = await self._embedding_encode(cnt)
                    chunks.append((cnt, embds))
            except TaskCanceledException:
                raise
            except Exception as exc:
                self._error_count += 1
                warn_msg = f"[RAPTOR] Skip cluster ({len(ck_idx)} chunks) due to error: {exc}"
                logging.warning(warn_msg)
                if callback:
                    callback(msg=warn_msg)
                if self._error_count >= self._max_errors:
                    raise RuntimeError(f"RAPTOR aborted after {self._error_count} errors. Last error: {exc}") from exc

        while end - start > 1:
            self._check_task_canceled(task_id, "layer processing")

            embeddings = [embd for _, embd in chunks[start:end]]
            if len(embeddings) == 2:
                await summarize([start, start + 1])
                if callback:
                    callback(msg="Cluster one layer: {} -> {}".format(end - start, len(chunks) - end))
                layers.append((end, len(chunks)))
                start = end
                end = len(chunks)
                continue

            n_neighbors = int((len(embeddings) - 1) ** 0.8)
            reduced_embeddings = umap.UMAP(
                n_neighbors=max(2, n_neighbors),
                n_components=min(12, len(embeddings) - 2),
                metric="cosine",
            ).fit_transform(embeddings)
            n_clusters = self._get_optimal_clusters(reduced_embeddings, random_state, task_id=task_id)
            if n_clusters == 1:
                lbls = [0 for _ in range(len(reduced_embeddings))]
            else:
                gm = GaussianMixture(n_components=n_clusters, random_state=random_state)
                gm.fit(reduced_embeddings)
                probs = gm.predict_proba(reduced_embeddings)
                lbls = [np.where(prob > self._threshold)[0] for prob in probs]
                lbls = [lbl[0] if isinstance(lbl, np.ndarray) else lbl for lbl in lbls]

            tasks = []
            for c in range(n_clusters):
                ck_idx = [i + start for i in range(len(lbls)) if lbls[i] == c]
                assert len(ck_idx) > 0
                self._check_task_canceled(task_id, "before cluster processing")
                tasks.append(asyncio.create_task(summarize(ck_idx)))
            try:
                await asyncio.gather(*tasks, return_exceptions=False)
            except Exception as e:
                logging.error(f"Error in RAPTOR cluster processing: {e}")
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise

            assert len(chunks) - end == n_clusters, "{} vs. {}".format(len(chunks) - end, n_clusters)
            layers.append((end, len(chunks)))
            if callback:
                callback(msg="Cluster one layer: {} -> {}".format(end - start, len(chunks) - end))
            start = end
            end = len(chunks)

        return chunks
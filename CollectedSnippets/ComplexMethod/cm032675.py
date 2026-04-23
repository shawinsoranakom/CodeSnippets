async def __call__(self, graph: nx.Graph,
                       subgraph_nodes: set[str],
                       prompt_variables: dict[str, Any] | None = None,
                       callback: Callable | None = None,
                       task_id: str = "") -> EntityResolutionResult:
        """Call method definition."""
        if prompt_variables is None:
            prompt_variables = {}

        # Wire defaults into the prompt variables
        self.prompt_variables = {
            **prompt_variables,
            self._record_delimiter_key: prompt_variables.get(self._record_delimiter_key)
                                        or DEFAULT_RECORD_DELIMITER,
            self._entity_index_delimiter_key: prompt_variables.get(self._entity_index_delimiter_key)
                                              or DEFAULT_ENTITY_INDEX_DELIMITER,
            self._resolution_result_delimiter_key: prompt_variables.get(self._resolution_result_delimiter_key)
                                                   or DEFAULT_RESOLUTION_RESULT_DELIMITER,
        }

        nodes = sorted(graph.nodes())
        entity_types = sorted(set(graph.nodes[node].get('entity_type', '-') for node in nodes))
        node_clusters = {entity_type: [] for entity_type in entity_types}

        for node in nodes:
            node_clusters[graph.nodes[node].get('entity_type', '-')].append(node)

        candidate_resolution = {entity_type: [] for entity_type in entity_types}
        for k, v in node_clusters.items():
            candidate_resolution[k] = [(a, b) for a, b in itertools.combinations(v, 2) if (a in subgraph_nodes or b in subgraph_nodes) and self.is_similarity(a, b)]
        num_candidates = sum([len(candidates) for _, candidates in candidate_resolution.items()])
        callback(msg=f"Identified {num_candidates} candidate pairs")
        remain_candidates_to_resolve = num_candidates

        resolution_result = set()
        resolution_result_lock = asyncio.Lock()
        resolution_batch_size = 100
        max_concurrent_tasks = 5
        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        async def limited_resolve_candidate(candidate_batch, result_set, result_lock):
            nonlocal remain_candidates_to_resolve, callback
            async with semaphore:
                try:
                    enable_timeout_assertion = os.environ.get("ENABLE_TIMEOUT_ASSERTION")
                    timeout_sec = 280 if enable_timeout_assertion else 1_000_000_000

                    try:
                        await asyncio.wait_for(
                            self._resolve_candidate(candidate_batch, result_set, result_lock, task_id),
                            timeout=timeout_sec
                        )
                        remain_candidates_to_resolve -= len(candidate_batch[1])
                        callback(
                            msg=f"Resolved {len(candidate_batch[1])} pairs, "
                                f"{remain_candidates_to_resolve} remain."
                        )

                    except asyncio.TimeoutError:
                        logging.warning(f"Timeout resolving {candidate_batch}, skipping...")
                        remain_candidates_to_resolve -= len(candidate_batch[1])
                        callback(
                            msg=f"Failed to resolve {len(candidate_batch[1])} pairs due to timeout, skipped. "
                                f"{remain_candidates_to_resolve} remain."
                        )

                except Exception as exception:
                    logging.error(f"Error resolving candidate batch: {exception}")


        tasks = []
        for key, lst in candidate_resolution.items():
            if not lst:
                continue
            for i in range(0, len(lst), resolution_batch_size):
                batch = (key, lst[i:i + resolution_batch_size])
                tasks.append(limited_resolve_candidate(batch, resolution_result, resolution_result_lock))
        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception as e:
            logging.error(f"Error resolving candidate pairs: {e}")
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        callback(msg=f"Resolved {num_candidates} candidate pairs, {len(resolution_result)} of them are selected to merge.")

        change = GraphChange()
        connect_graph = nx.Graph()
        connect_graph.add_edges_from(resolution_result)

        merge_lock = asyncio.Lock()

        async def limited_merge_nodes(graph, nodes, change):
            async with merge_lock:
                await self._merge_graph_nodes(graph, nodes, change, task_id)

        tasks = []
        for sub_connect_graph in nx.connected_components(connect_graph):
            merging_nodes = list(sub_connect_graph)
            tasks.append(asyncio.create_task(limited_merge_nodes(graph, merging_nodes, change)))
        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception as e:
            logging.error(f"Error merging nodes: {e}")
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        # Update pagerank
        pr = nx.pagerank(graph)
        for node_name, pagerank in pr.items():
            graph.nodes[node_name]["pagerank"] = pagerank

        return EntityResolutionResult(
            graph=graph,
            change=change,
        )
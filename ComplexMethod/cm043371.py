async def traverse(self,
                      start_url: str,
                      crawler: AsyncWebCrawler,
                      config: CrawlerRunConfig) -> RunManyReturn:
        """Non-blocking BFS with O(b^d) time complexity awareness"""
        ctx = TraversalContext(self.priority_fn)
        ctx.frontier.insert(self.priority_fn(start_url), (start_url, None, 0))
        ctx.visited.add(start_url)
        ctx.depths[start_url] = 0

        while not ctx.frontier.is_empty() and not self._cancel.is_set():
            # Use the best algorith, to find top_n value
            top_n = calculate_quantum_batch_size(
                depth=ctx.current_depth,
                max_depth=self.max_depth,
                frontier_size=len(ctx.frontier._heap),
                visited_size=len(ctx.visited)
            )

            urls = ctx.frontier.extract(top_n=top_n)
            # url, parent, depth = ctx.frontier.extract(top_n=top_n)
            if urls:
                ctx.current_depth = urls[0][2]

            async with self.semaphore:
                results = await collect_many_results([url for (url, parent, depth) in urls], crawler, config)
                # results = await asyncio.gather(*[
                #     collect_results(url, crawler, config) for (url, parent, depth) in urls
                # ])
                # result = _result[0]
                for ix, result in enumerate(results):
                    url, parent, depth = result.url, urls[ix][1], urls[ix][2]
                    result.metadata['depth'] = depth
                    result.metadata['parent'] = parent
                    yield result

                    if depth < self.max_depth:
                        async for link in self.link_hypercube(result):
                            if link not in ctx.visited:
                                priority = self.priority_fn(link)
                                ctx.frontier.insert(priority, (link, url, depth + 1))
                                ctx.visited.add(link)
                                ctx.depths[link] = depth + 1
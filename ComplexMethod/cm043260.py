async def digest(self, 
                               start_url: str, 
                               query: str,
                               resume_from: Optional[str] = None) -> CrawlState:
        """Main entry point for adaptive crawling"""
        # Initialize or resume state
        if resume_from:
            self.state = CrawlState.load(resume_from)
            self.state.query = query  # Update query in case it changed
        else:
            self.state = CrawlState(
                crawled_urls=set(),
                knowledge_base=[],
                pending_links=[],
                query=query,
                metrics={}
            )

        # Create crawler if needed
        if not self.crawler:
            self.crawler = AsyncWebCrawler()
            await self.crawler.__aenter__()

        self.strategy.config = self.config  # Pass config to strategy

        # If using embedding strategy and not resuming, expand query space
        if isinstance(self.strategy, EmbeddingStrategy) and not resume_from:
            # Generate query space
            query_embeddings, expanded_queries = await self.strategy.map_query_semantic_space(
                query, 
                self.config.n_query_variations
            )
            self.state.query_embeddings = query_embeddings
            self.state.expanded_queries = expanded_queries[1:]  # Skip original query
            self.state.embedding_model = self.strategy.embedding_model

        try:
            # Initial crawl if not resuming
            if start_url not in self.state.crawled_urls:
                result = await self._crawl_with_preview(start_url, query)
                if result and hasattr(result, 'success') and result.success:
                    self.state.knowledge_base.append(result)
                    self.state.crawled_urls.add(start_url)
                    # Extract links from result - handle both dict and Links object formats
                    if hasattr(result, 'links') and result.links:
                        if isinstance(result.links, dict):
                            # Extract internal and external links from dict
                            internal_links = [Link(**link) for link in result.links.get('internal', [])]
                            external_links = [Link(**link) for link in result.links.get('external', [])]
                            self.state.pending_links.extend(internal_links + external_links)
                        else:
                            # Handle Links object
                            self.state.pending_links.extend(result.links.internal + result.links.external)

                    # Update state
                    await self.strategy.update_state(self.state, [result])

            # adaptive expansion
            depth = 0
            while depth < self.config.max_depth:
                # Calculate confidence
                confidence = await self.strategy.calculate_confidence(self.state)
                self.state.metrics['confidence'] = confidence

                # Check stopping criteria
                if await self.strategy.should_stop(self.state, self.config):
                    break

                # Rank candidate links
                ranked_links = await self.strategy.rank_links(self.state, self.config)

                if not ranked_links:
                    break

                # Check minimum gain threshold
                if ranked_links[0][1] < self.config.min_gain_threshold:
                    break

                # Select top K links
                to_crawl = [(link, score) for link, score in ranked_links[:self.config.top_k_links]
                           if link.href not in self.state.crawled_urls]

                if not to_crawl:
                    break

                # Crawl selected links
                new_results = await self._crawl_batch(to_crawl, query)

                if new_results:
                    # Update knowledge base
                    self.state.knowledge_base.extend(new_results)

                    # Update crawled URLs and pending links
                    for result, (link, _) in zip(new_results, to_crawl):
                        if result:
                            self.state.crawled_urls.add(link.href)
                            # Extract links from result - handle both dict and Links object formats
                            if hasattr(result, 'links') and result.links:
                                new_links = []
                                if isinstance(result.links, dict):
                                    # Extract internal and external links from dict
                                    internal_links = [Link(**link_data) for link_data in result.links.get('internal', [])]
                                    external_links = [Link(**link_data) for link_data in result.links.get('external', [])]
                                    new_links = internal_links + external_links
                                else:
                                    # Handle Links object
                                    new_links = result.links.internal + result.links.external

                                # Add new links to pending
                                for new_link in new_links:
                                    if new_link.href not in self.state.crawled_urls:
                                        self.state.pending_links.append(new_link)

                    # Update state with new results
                    await self.strategy.update_state(self.state, new_results)

                depth += 1

                # Save state if configured
                if self.config.save_state and self.config.state_path:
                    self.state.save(self.config.state_path)

            # Final confidence calculation
            learning_score = await self.strategy.calculate_confidence(self.state)

            # For embedding strategy, get quality-based confidence
            if isinstance(self.strategy, EmbeddingStrategy):
                self.state.metrics['confidence'] = self.strategy.get_quality_confidence(self.state)
            else:
                # For statistical strategy, use the same as before
                self.state.metrics['confidence'] = learning_score

            self.state.metrics['pages_crawled'] = len(self.state.crawled_urls)
            self.state.metrics['depth_reached'] = depth

            # Final save
            if self.config.save_state and self.config.state_path:
                self.state.save(self.config.state_path)

            return self.state

        finally:
            # Cleanup if we created the crawler
            if self._owns_crawler and self.crawler:
                await self.crawler.__aexit__(None, None, None)
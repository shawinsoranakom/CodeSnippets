async def test_confidence_progression(self):
        """Test confidence calculation as we crawl each URL"""
        print(f"Testing confidence for query: '{self.query}'")
        print("=" * 80)

        # Initialize state
        state = CrawlState(query=self.query)

        # Create crawler
        async with AsyncWebCrawler() as crawler:
            for i, url in enumerate(self.test_urls, 1):
                print(f"\n{i}. Crawling: {url}")
                print("-" * 80)

                # Crawl the URL
                result = await crawler.arun(url=url)

                # Extract markdown content
                if hasattr(result, '_results') and result._results:
                    result = result._results[0]

                # Create a mock CrawlResult with markdown
                mock_result = type('CrawlResult', (), {
                    'markdown': type('Markdown', (), {
                        'raw_markdown': result.markdown.raw_markdown if hasattr(result, 'markdown') else ''
                    })(),
                    'url': url
                })()

                # Update state
                state.knowledge_base.append(mock_result)
                await self.strategy.update_state(state, [mock_result])

                # Calculate metrics
                confidence = await self.strategy.calculate_confidence(state)

                # Get individual components
                coverage = state.metrics.get('coverage', 0)
                consistency = state.metrics.get('consistency', 0)
                saturation = state.metrics.get('saturation', 0)

                # Analyze term frequencies
                query_terms = self.strategy._tokenize(self.query.lower())
                term_stats = {}
                for term in query_terms:
                    term_stats[term] = {
                        'tf': state.term_frequencies.get(term, 0),
                        'df': state.document_frequencies.get(term, 0)
                    }

                # Print detailed results
                print(f"State after crawl {i}:")
                print(f"  Total documents: {state.total_documents}")
                print(f"  Unique terms: {len(state.term_frequencies)}")
                print(f"  New terms added: {state.new_terms_history[-1] if state.new_terms_history else 0}")

                print(f"\nQuery term statistics:")
                for term, stats in term_stats.items():
                    print(f"  '{term}': tf={stats['tf']}, df={stats['df']}")

                print(f"\nMetrics:")
                print(f"  Coverage: {coverage:.3f}")
                print(f"  Consistency: {consistency:.3f}")
                print(f"  Saturation: {saturation:.3f}")
                print(f"  → Confidence: {confidence:.3f}")

                # Show coverage calculation details
                print(f"\nCoverage calculation details:")
                self._debug_coverage_calculation(state, query_terms)

                # Alert if confidence decreased
                if i > 1 and confidence < state.metrics.get('prev_confidence', 0):
                    print(f"\n⚠️  WARNING: Confidence decreased from {state.metrics.get('prev_confidence', 0):.3f} to {confidence:.3f}")

                state.metrics['prev_confidence'] = confidence
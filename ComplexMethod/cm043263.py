def print_stats(self, detailed: bool = False) -> None:
        """Print comprehensive statistics about the knowledge base

        Args:
            detailed: If True, show detailed statistics including top terms
        """
        if not self.state:
            print("No crawling state available.")
            return

        # Import here to avoid circular imports
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            use_rich = True
        except ImportError:
            use_rich = False

        if not detailed and use_rich:
            # Summary view with nice table (like original)
            table = Table(title=f"Adaptive Crawl Stats - Query: '{self.state.query}'")
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Basic stats
            stats = self.coverage_stats
            table.add_row("Pages Crawled", str(stats.get('pages_crawled', 0)))
            table.add_row("Unique Terms", str(stats.get('unique_terms', 0)))
            table.add_row("Total Terms", str(stats.get('total_terms', 0)))
            table.add_row("Content Length", f"{stats.get('total_content_length', 0):,} chars")
            table.add_row("Pending Links", str(stats.get('pending_links', 0)))
            table.add_row("", "")  # Spacer

            # Strategy-specific metrics
            if isinstance(self.strategy, EmbeddingStrategy):
                # Embedding-specific metrics
                table.add_row("Confidence", f"{stats.get('confidence', 0):.2%}")
                table.add_row("Avg Min Distance", f"{self.state.metrics.get('avg_min_distance', 0):.3f}")
                table.add_row("Avg Close Neighbors", f"{self.state.metrics.get('avg_close_neighbors', 0):.1f}")
                table.add_row("Validation Score", f"{self.state.metrics.get('validation_confidence', 0):.2%}")
                table.add_row("", "")  # Spacer
                table.add_row("Is Sufficient?", "[green]Yes (Validated)[/green]" if self.is_sufficient else "[red]No[/red]")
            else:
                # Statistical strategy metrics
                table.add_row("Confidence", f"{stats.get('confidence', 0):.2%}")
                table.add_row("Coverage", f"{stats.get('coverage', 0):.2%}")
                table.add_row("Consistency", f"{stats.get('consistency', 0):.2%}")
                table.add_row("Saturation", f"{stats.get('saturation', 0):.2%}")
                table.add_row("", "")  # Spacer
                table.add_row("Is Sufficient?", "[green]Yes[/green]" if self.is_sufficient else "[red]No[/red]")

            console.print(table)
        else:
            # Detailed view or fallback when rich not available
            print("\n" + "="*80)
            print(f"Adaptive Crawl Statistics - Query: '{self.state.query}'")
            print("="*80)

            # Basic stats
            print("\n[*] Basic Statistics:")
            print(f"  Pages Crawled: {len(self.state.crawled_urls)}")
            print(f"  Pending Links: {len(self.state.pending_links)}")
            print(f"  Total Documents: {self.state.total_documents}")

            # Content stats
            total_content_length = sum(
                len(self._get_content_from_result(result))
                for result in self.state.knowledge_base
            )
            total_words = sum(self.state.term_frequencies.values())
            unique_terms = len(self.state.term_frequencies)

            print(f"\n[*] Content Statistics:")
            print(f"  Total Content: {total_content_length:,} characters")
            print(f"  Total Words: {total_words:,}")
            print(f"  Unique Terms: {unique_terms:,}")
            if total_words > 0:
                print(f"  Vocabulary Richness: {unique_terms/total_words:.2%}")

            # Strategy-specific output
            if isinstance(self.strategy, EmbeddingStrategy):
                # Semantic coverage for embedding strategy
                print(f"\n[*] Semantic Coverage Analysis:")
                print(f"  Average Min Distance: {self.state.metrics.get('avg_min_distance', 0):.3f}")
                print(f"  Avg Close Neighbors (< 0.3): {self.state.metrics.get('avg_close_neighbors', 0):.1f}")
                print(f"  Avg Very Close Neighbors (< 0.2): {self.state.metrics.get('avg_very_close_neighbors', 0):.1f}")

                # Confidence metrics
                print(f"\n[*] Confidence Metrics:")
                if self.is_sufficient:
                    if use_rich:
                        console.print(f"  Overall Confidence: {self.confidence:.2%} [green][VALIDATED][/green]")
                    else:
                        print(f"  Overall Confidence: {self.confidence:.2%} [VALIDATED]")
                else:
                    if use_rich:
                        console.print(f"  Overall Confidence: {self.confidence:.2%} [red][NOT VALIDATED][/red]")
                    else:
                        print(f"  Overall Confidence: {self.confidence:.2%} [NOT VALIDATED]")

                print(f"  Learning Score: {self.state.metrics.get('learning_score', 0):.2%}")
                print(f"  Validation Score: {self.state.metrics.get('validation_confidence', 0):.2%}")

            else:
                # Query coverage for statistical strategy
                print(f"\n[*] Query Coverage:")
                query_terms = self.strategy._tokenize(self.state.query.lower())
                for term in query_terms:
                    tf = self.state.term_frequencies.get(term, 0)
                    df = self.state.document_frequencies.get(term, 0)
                    if df > 0:
                        if use_rich:
                            console.print(f"  '{term}': found in {df}/{self.state.total_documents} docs ([green]{df/self.state.total_documents:.0%}[/green]), {tf} occurrences")
                        else:
                            print(f"  '{term}': found in {df}/{self.state.total_documents} docs ({df/self.state.total_documents:.0%}), {tf} occurrences")
                    else:
                        if use_rich:
                            console.print(f"  '{term}': [red][X] not found[/red]")
                        else:
                            print(f"  '{term}': [X] not found")

                # Confidence metrics
                print(f"\n[*] Confidence Metrics:")
                status = "[OK]" if self.is_sufficient else "[!!]"
                if use_rich:
                    status_colored = "[green][OK][/green]" if self.is_sufficient else "[red][!!][/red]"
                    console.print(f"  Overall Confidence: {self.confidence:.2%} {status_colored}")
                else:
                    print(f"  Overall Confidence: {self.confidence:.2%} {status}")
                print(f"  Coverage Score: {self.state.metrics.get('coverage', 0):.2%}")
                print(f"  Consistency Score: {self.state.metrics.get('consistency', 0):.2%}")
                print(f"  Saturation Score: {self.state.metrics.get('saturation', 0):.2%}")

            # Crawl efficiency
            if self.state.new_terms_history:
                avg_new_terms = sum(self.state.new_terms_history) / len(self.state.new_terms_history)
                print(f"\n[*] Crawl Efficiency:")
                print(f"  Avg New Terms per Page: {avg_new_terms:.1f}")
                print(f"  Information Saturation: {self.state.metrics.get('saturation', 0):.2%}")

            if detailed:
                print("\n" + "-"*80)
                if use_rich:
                    console.print("[bold cyan]DETAILED STATISTICS[/bold cyan]")
                else:
                    print("DETAILED STATISTICS")
                print("-"*80)

                # Top terms
                print("\n[+] Top 20 Terms by Frequency:")
                top_terms = sorted(self.state.term_frequencies.items(), key=lambda x: x[1], reverse=True)[:20]
                for i, (term, freq) in enumerate(top_terms, 1):
                    df = self.state.document_frequencies.get(term, 0)
                    if use_rich:
                        console.print(f"  {i:2d}. [yellow]'{term}'[/yellow]: {freq} occurrences in {df} docs")
                    else:
                        print(f"  {i:2d}. '{term}': {freq} occurrences in {df} docs")

                # URLs crawled
                print(f"\n[+] URLs Crawled ({len(self.state.crawled_urls)}):")
                for i, url in enumerate(self.state.crawl_order, 1):
                    new_terms = self.state.new_terms_history[i-1] if i <= len(self.state.new_terms_history) else 0
                    if use_rich:
                        console.print(f"  {i}. [cyan]{url}[/cyan]")
                        console.print(f"     -> Added [green]{new_terms}[/green] new terms")
                    else:
                        print(f"  {i}. {url}")
                        print(f"     -> Added {new_terms} new terms")

                # Document frequency distribution
                print("\n[+] Document Frequency Distribution:")
                df_counts = {}
                for df in self.state.document_frequencies.values():
                    df_counts[df] = df_counts.get(df, 0) + 1

                for df in sorted(df_counts.keys()):
                    count = df_counts[df]
                    print(f"  Terms in {df} docs: {count} terms")

                # Embedding stats
                if self.state.embedding_model:
                    print("\n[+] Semantic Coverage Analysis:")
                    print(f"  Embedding Model: {self.state.embedding_model}")
                    print(f"  Query Variations: {len(self.state.expanded_queries)}")
                    if self.state.kb_embeddings is not None:
                        print(f"  Knowledge Embeddings: {self.state.kb_embeddings.shape}")
                    else:
                        print(f"  Knowledge Embeddings: None")
                    print(f"  Semantic Gaps: {len(self.state.semantic_gaps)}")
                    print(f"  Coverage Achievement: {self.confidence:.2%}")

                    # Show sample expanded queries
                    if self.state.expanded_queries:
                        print("\n[+] Query Space (samples):")
                        for i, eq in enumerate(self.state.expanded_queries[:5], 1):
                            if use_rich:
                                console.print(f"  {i}. [yellow]{eq}[/yellow]")
                            else:
                                print(f"  {i}. {eq}")

            print("\n" + "="*80)
async def main():
    """Run all embedding strategy tests"""
    console.print("[bold magenta]Embedding-based Adaptive Crawler Test Suite[/bold magenta]")
    console.print("=" * 60)

    try:
        # Check if we have required dependencies
        has_sentence_transformers = True
        has_numpy = True

        try:
            import numpy
            console.print("[green]✓ NumPy installed[/green]")
        except ImportError:
            has_numpy = False
            console.print("[red]Missing numpy[/red]")

        # Try to import sentence_transformers but catch numpy compatibility errors
        try:
            import sentence_transformers
            console.print("[green]✓ Sentence-transformers installed[/green]")
        except (ImportError, RuntimeError, ValueError) as e:
            has_sentence_transformers = False
            console.print(f"[yellow]Warning: sentence-transformers not available[/yellow]")
            console.print("[yellow]Tests will use OpenAI embeddings if available or mock data[/yellow]")

        # Run tests based on available dependencies
        if has_numpy:
            # Check if we should use OpenAI for embeddings
            use_openai = not has_sentence_transformers and os.getenv('OPENAI_API_KEY')

            if not has_sentence_transformers and not os.getenv('OPENAI_API_KEY'):
                console.print("\n[red]Neither sentence-transformers nor OpenAI API key available[/red]")
                console.print("[yellow]Please set OPENAI_API_KEY or fix sentence-transformers installation[/yellow]")
                return

            # Run all tests
            # await test_basic_embedding_crawl()
            # await test_embedding_vs_statistical(use_openai=use_openai)

            # Run the fast convergence test - this is the most important one
            # await test_fast_convergence_with_relevant_query()

            # Test with irrelevant query
            await test_irrelevant_query_behavior()

            # Only run OpenAI-specific test if we have API key
            # if os.getenv('OPENAI_API_KEY'):
            #     await test_custom_embedding_provider()

            # # Skip tests that require sentence-transformers when it's not available
            # if has_sentence_transformers:
            #     await test_knowledge_export_import()
            #     await test_gap_visualization()
            # else:
            #     console.print("\n[yellow]Skipping tests that require sentence-transformers due to numpy compatibility issues[/yellow]")

            # This test should work with mock data
            # await test_high_dimensional_handling()
        else:
            console.print("\n[red]Cannot run tests without NumPy[/red]")
            return

        console.print("\n[bold green]✅ All tests completed![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed: {e}[/bold red]")
        import traceback
        traceback.print_exc()
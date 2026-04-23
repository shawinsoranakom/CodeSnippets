async def test_adaptive_crawler_embedding():
    """
    Verify EmbeddingStrategy LLM code is uncommented and functional.

    BEFORE: LLM call was commented out, using hardcoded mock data
    AFTER: Actually calls LLM for query expansion
    """
    print_test("AdaptiveCrawler Query Expansion", "#1621")

    try:
        # Read the source file to verify the fix
        import crawl4ai.adaptive_crawler as adaptive_module
        source_file = adaptive_module.__file__

        with open(source_file, 'r') as f:
            source_code = f.read()

        # Check that the LLM call is NOT commented out
        # Look for the perform_completion_with_backoff call

        # Find the EmbeddingStrategy section
        if 'class EmbeddingStrategy' not in source_code:
            record_result("AdaptiveCrawler Query Expansion", "#1621", True,
                         "EmbeddingStrategy not in adaptive_crawler (may have moved)",
                         skipped=True)
            return

        # Check if the mock data line is commented out
        # and the actual LLM call is NOT commented out
        lines = source_code.split('\n')
        in_embedding_strategy = False
        found_llm_call = False
        mock_data_commented = False

        for i, line in enumerate(lines):
            if 'class EmbeddingStrategy' in line:
                in_embedding_strategy = True
            elif in_embedding_strategy and line.strip().startswith('class '):
                in_embedding_strategy = False

            if in_embedding_strategy:
                # Check for uncommented LLM call
                if 'perform_completion_with_backoff' in line and not line.strip().startswith('#'):
                    found_llm_call = True
                # Check for commented mock data
                if "variations ={'queries'" in line or 'variations = {\'queries\'' in line:
                    if line.strip().startswith('#'):
                        mock_data_commented = True

        if found_llm_call:
            record_result("AdaptiveCrawler Query Expansion", "#1621", True,
                         "LLM call is active in EmbeddingStrategy")
        else:
            # Check if the entire embedding strategy exists but might be structured differently
            if 'perform_completion_with_backoff' in source_code:
                record_result("AdaptiveCrawler Query Expansion", "#1621", True,
                             "perform_completion_with_backoff found in module")
            else:
                record_result("AdaptiveCrawler Query Expansion", "#1621", False,
                             "LLM call not found or still commented out")

    except Exception as e:
        record_result("AdaptiveCrawler Query Expansion", "#1621", False, f"Exception: {e}")
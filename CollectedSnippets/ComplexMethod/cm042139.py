def _print_bm_result(result):
        import pandas as pd

        metrics = [
            item["metrics"]
            for item in result
            if item["log"]["generated_text"] != LLM_ERROR and item["log"]["generated_text"] != EMPTY_ERROR
        ]

        data = pd.DataFrame(metrics)
        logger.info(f"\n {data.mean()}")

        llm_errors = [item for item in result if item["log"]["generated_text"] == LLM_ERROR]
        retrieve_errors = [item for item in result if item["log"]["generated_text"] == EMPTY_ERROR]
        logger.info(
            f"Percentage of retrieval failures due to incorrect LLM instruction following:"
            f" {100.0 * len(llm_errors) / len(result)}%"
        )
        logger.info(
            f"Percentage of retrieval failures due to retriever not recalling any documents is:"
            f" {100.0 * len(retrieve_errors) / len(result)}%"
        )
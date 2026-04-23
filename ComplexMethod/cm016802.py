def test_sequential_different_methods(self, client, graph):
        """
        Execute multiple prompts sequentially with different preview methods.
        Each should complete independently with correct preview behavior.
        """
        methods = ["latent2rgb", "none", "default"]
        results = []

        for method in methods:
            # Randomize seed for each execution to avoid caching
            graph_run = randomize_seed(graph)
            extra_data = {"preview_method": method}
            response = client.queue_prompt(graph_run, extra_data)

            result = client.wait_for_execution(response["prompt_id"])
            results.append({
                "method": method,
                "completed": result["completed"],
                "preview_count": result["preview_count"],
                "execution_time": result["execution_time"],
                "error": result["error"]
            })

        # All should complete or have clear errors
        for r in results:
            assert r["completed"] or r["error"] is not None, \
                f"Method {r['method']} neither completed nor errored"

        # "none" should have zero previews if completed
        none_result = next(r for r in results if r["method"] == "none")
        if none_result["completed"]:
            assert none_result["preview_count"] == 0, \
                f"'none' should have 0 previews, got {none_result['preview_count']}"

        print("\nSequential execution results:")  # noqa: T201
        for r in results:
            status = "✓" if r["completed"] else f"✗ ({r['error']})"
            print(f"  {r['method']}: {status}, {r['preview_count']} previews, {r['execution_time']:.2f}s")
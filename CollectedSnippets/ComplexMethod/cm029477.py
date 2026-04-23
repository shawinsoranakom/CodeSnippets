async def _remove_background(self, args: Dict[str, Any]) -> ToolExecutionResult:
        if not REPLICATE_API_KEY:
            return ToolExecutionResult(
                ok=False,
                result={"error": "Background removal requires REPLICATE_API_KEY."},
                summary={"error": "Missing Replicate API key"},
            )

        image_urls = args.get("image_urls") or []
        if not isinstance(image_urls, list) or not image_urls:
            return ToolExecutionResult(
                ok=False,
                result={
                    "error": "remove_background requires a non-empty image_urls list"
                },
                summary={"error": "Missing image_urls"},
            )

        cleaned = [url.strip() for url in image_urls if isinstance(url, str)]
        unique_urls = list(dict.fromkeys([u for u in cleaned if u]))
        if not unique_urls:
            return ToolExecutionResult(
                ok=False,
                result={"error": "No valid image URLs provided"},
                summary={"error": "No valid image_urls"},
            )

        batch_size = 20
        raw_results: list[str | BaseException] = []
        for i in range(0, len(unique_urls), batch_size):
            batch = unique_urls[i : i + batch_size]
            tasks = [remove_background(url, REPLICATE_API_KEY) for url in batch]
            raw_results.extend(await asyncio.gather(*tasks, return_exceptions=True))

        results: List[Dict[str, Any]] = []
        for url, raw in zip(unique_urls, raw_results):
            if isinstance(raw, BaseException):
                print(f"Background removal failed for {url}: {raw}")
                results.append(
                    {"image_url": url, "result_url": None, "status": "error"}
                )
            else:
                results.append(
                    {"image_url": url, "result_url": raw, "status": "ok"}
                )

        summary_items = [
            {
                "image_url": summarize_text(r["image_url"], 100),
                "result_url": r["result_url"],
                "status": r["status"],
            }
            for r in results
        ]
        return ToolExecutionResult(
            ok=True,
            result={"images": results},
            summary={"images": summary_items},
        )
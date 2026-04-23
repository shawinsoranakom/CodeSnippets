async def _generate_images(self, args: Dict[str, Any]) -> ToolExecutionResult:
        if not self.should_generate_images:
            return ToolExecutionResult(
                ok=False,
                result={"error": "Image generation is disabled."},
                summary={"error": "Image generation disabled"},
            )

        prompts = args.get("prompts") or []
        if not isinstance(prompts, list) or not prompts:
            return ToolExecutionResult(
                ok=False,
                result={"error": "generate_images requires a non-empty prompts list"},
                summary={"error": "Missing prompts"},
            )

        cleaned = [prompt.strip() for prompt in prompts if isinstance(prompt, str)]
        unique_prompts = list(dict.fromkeys([p for p in cleaned if p]))
        if not unique_prompts:
            return ToolExecutionResult(
                ok=False,
                result={"error": "No valid prompts provided"},
                summary={"error": "No valid prompts"},
            )
        if REPLICATE_API_KEY:
            model = "flux"
            api_key = REPLICATE_API_KEY
            base_url = None
        else:
            if not self.openai_api_key:
                return ToolExecutionResult(
                    ok=False,
                    result={"error": "No API key available for image generation."},
                    summary={"error": "Missing image generation API key"},
                )
            model = "dalle3"
            api_key = self.openai_api_key
            base_url = self.openai_base_url

        generated = await process_tasks(unique_prompts, api_key, base_url, model)  # type: ignore
        merged_results = {
            prompt: url for prompt, url in zip(unique_prompts, generated)
        }
        summary_items = [
            {
                "prompt": prompt,
                "url": url,
                "status": "ok" if url else "error",
            }
            for prompt, url in merged_results.items()
        ]
        result = {"images": merged_results}
        summary = {"images": summary_items}
        return ToolExecutionResult(ok=True, result=result, summary=summary)
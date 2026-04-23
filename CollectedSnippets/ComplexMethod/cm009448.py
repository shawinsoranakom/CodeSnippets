async def abatch(
        self,
        inputs: list[LanguageModelInput],
        config: RunnableConfig | list[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Any,
    ) -> list[str]:
        if not inputs:
            return []
        config = get_config_list(config, len(inputs))
        max_concurrency = config[0].get("max_concurrency")

        if max_concurrency is None:
            try:
                llm_result = await self.agenerate_prompt(
                    [self._convert_input(input_) for input_ in inputs],
                    callbacks=[c.get("callbacks") for c in config],
                    tags=[c.get("tags") for c in config],
                    metadata=[c.get("metadata") for c in config],
                    run_name=[c.get("run_name") for c in config],
                    **kwargs,
                )
                return [g[0].text for g in llm_result.generations]
            except Exception as e:
                if return_exceptions:
                    return cast("list[str]", [e for _ in inputs])
                raise
        else:
            batches = [
                inputs[i : i + max_concurrency]
                for i in range(0, len(inputs), max_concurrency)
            ]
            config = [{**c, "max_concurrency": None} for c in config]
            return [
                output
                for i, batch in enumerate(batches)
                for output in await self.abatch(
                    batch,
                    config=config[i * max_concurrency : (i + 1) * max_concurrency],
                    return_exceptions=return_exceptions,
                    **kwargs,
                )
            ]
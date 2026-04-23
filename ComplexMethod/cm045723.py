async def __wrapped__(self, inputs: list[str], **kwargs) -> list[np.ndarray]:
        """Embed the documents

        Args:
            inputs: mandatory, the strings to embed.
            **kwargs: optional parameters, if unset defaults from the constructor
              will be taken.
        #"""
        import openai

        if self.client is None:
            self.client = openai.AsyncOpenAI(api_key=self.api_key, max_retries=0)

        kwargs = _extract_value_inside_dict(kwargs)

        if kwargs.get("model") is None and self.kwargs.get("model") is None:
            raise ValueError(
                "`model` parameter is missing in `OpenAIEmbedder`. "
                "Please provide the model name either in the constructor or in the function call."
            )

        constant_kwargs, per_row_kwargs = _split_batched_kwargs(kwargs)
        constant_kwargs = {**self.kwargs, **constant_kwargs}

        if self.truncation_keep_strategy:
            if "model" in per_row_kwargs:
                inputs = [
                    self.truncate_context(model, input, self.truncation_keep_strategy)
                    for (model, input) in zip(per_row_kwargs["model"], inputs)
                ]
            else:
                inputs = [
                    self.truncate_context(
                        constant_kwargs["model"], input, self.truncation_keep_strategy
                    )
                    for input in inputs
                ]

        # if kwargs are not the same for every input we cannot batch them
        if per_row_kwargs:

            async def embed_single(input, kwargs) -> np.ndarray:
                kwargs = {**constant_kwargs, **kwargs}
                ret = await self.client.embeddings.create(input=[input], **kwargs)  # type: ignore
                return np.array(ret.data[0].embedding)

            list_of_per_row_kwargs = [
                dict(zip(per_row_kwargs, values))
                for values in zip(*per_row_kwargs.values())
            ]
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(embed_single(input, kwargs))
                    for input, kwargs in zip(inputs, list_of_per_row_kwargs)
                ]

            result_list = [task.result() for task in tasks]
            return result_list

        else:
            ret = await self.client.embeddings.create(input=inputs, **constant_kwargs)
            return [np.array(datum.embedding) for datum in ret.data]
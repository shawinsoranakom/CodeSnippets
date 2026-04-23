async def _generator() -> AsyncGenerator[Union[str, CreateResult], None]:
            cached_result, cache_key = self._check_cache(
                messages,
                tools,
                json_output,
                extra_create_args,
            )
            if cached_result is not None:
                if isinstance(cached_result, list):
                    # Cache hit from previous streaming call
                    for result in cached_result:
                        if isinstance(result, CreateResult):
                            result.cached = True
                        yield result
                    return
                elif isinstance(cached_result, CreateResult):
                    # Cache hit from previous non-streaming call - convert to streaming format
                    cached_result.cached = True

                    # If content is a non-empty string, yield it as a streaming chunk first
                    if isinstance(cached_result.content, str) and cached_result.content:
                        yield cached_result.content

                    yield cached_result
                    return

            result_stream = self.client.create_stream(
                messages,
                tools=tools,
                json_output=json_output,
                tool_choice=tool_choice,
                extra_create_args=extra_create_args,
                cancellation_token=cancellation_token,
            )

            output_results: List[Union[str, CreateResult]] = []

            async for result in result_stream:
                output_results.append(result)
                yield result

            # Store the complete results only after streaming is finished
            self.store.set(cache_key, output_results)
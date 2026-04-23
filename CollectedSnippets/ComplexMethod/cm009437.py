async def _atransform(
        self, input: AsyncIterator[str | BaseMessage]
    ) -> AsyncIterator[T]:
        prev_parsed = None
        acc_gen: GenerationChunk | ChatGenerationChunk | None = None
        async for chunk in input:
            chunk_gen: GenerationChunk | ChatGenerationChunk
            if isinstance(chunk, BaseMessageChunk):
                chunk_gen = ChatGenerationChunk(message=chunk)
            elif isinstance(chunk, BaseMessage):
                chunk_gen = ChatGenerationChunk(
                    message=BaseMessageChunk(**chunk.model_dump())
                )
            else:
                chunk_gen = GenerationChunk(text=chunk)

            acc_gen = chunk_gen if acc_gen is None else acc_gen + chunk_gen  # type: ignore[operator]

            parsed = await self.aparse_result([acc_gen], partial=True)
            if parsed is not None and parsed != prev_parsed:
                if self.diff:
                    yield await run_in_executor(None, self._diff, prev_parsed, parsed)
                else:
                    yield parsed
                prev_parsed = parsed
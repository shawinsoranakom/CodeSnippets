def process_thinking_chunk(
        chunk: str, start_time: float = 0
    ) -> Tuple[float, List[Union[str, Reasoning]]]:
        """Process a thinking chunk and return timing and results."""
        results = []

        # Handle non-thinking chunk
        if not start_time and "<think>" not in chunk and "</think>" not in chunk:
            return 0, [chunk]

        # Handle thinking start
        if "<think>" in chunk and "`<think>`" not in chunk:
            before_think, *after = chunk.split("<think>", 1)

            if before_think:
                results.append(before_think)

            results.append(Reasoning(status="🤔 Is thinking...", is_thinking="<think>"))

            if after:
                if "</think>" in after[0]:
                    after, *after_end = after[0].split("</think>", 1)
                    results.append(Reasoning(after))
                    results.append(Reasoning(status="", is_thinking="</think>"))
                    if after_end:
                        results.append(after_end[0])
                    return 0, results
                else:
                    results.append(Reasoning(after[0]))

            return time.time(), results

        # Handle thinking end
        if "</think>" in chunk:
            before_end, *after = chunk.split("</think>", 1)

            if before_end:
                results.append(Reasoning(before_end))

            thinking_duration = time.time() - start_time if start_time > 0 else 0

            status = (
                f"Thought for {thinking_duration:.2f}s" if thinking_duration > 1 else ""
            )
            results.append(Reasoning(status=status, is_thinking="</think>"))

            # Make sure to handle text after the closing tag
            if after and after[0].strip():
                results.append(after[0])

            return 0, results

        # Handle ongoing thinking
        if start_time:
            return start_time, [Reasoning(chunk)]

        return start_time, [chunk]
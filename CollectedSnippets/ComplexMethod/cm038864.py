async def print_stream_response(
    stream_response: openai.AsyncStream[ChatCompletionChunk],
    title: str,
    args: argparse.Namespace,
):
    print(f"\n\n{title} (Streaming):")

    local_reasoning_header_printed = False
    local_content_header_printed = False

    async for chunk in stream_response:
        delta = chunk.choices[0].delta

        reasoning_chunk_text: str | None = getattr(delta, "reasoning", None)
        content_chunk_text = delta.content

        if args.reasoning:
            if reasoning_chunk_text:
                if not local_reasoning_header_printed:
                    print("  Reasoning: ", end="")
                    local_reasoning_header_printed = True
                print(reasoning_chunk_text, end="", flush=True)

            if content_chunk_text:
                if not local_content_header_printed:
                    if local_reasoning_header_printed:
                        print()
                    print("  Content: ", end="")
                    local_content_header_printed = True
                print(content_chunk_text, end="", flush=True)
        else:
            if content_chunk_text:
                if not local_content_header_printed:
                    print("  Content: ", end="")
                    local_content_header_printed = True
                print(content_chunk_text, end="", flush=True)
    print()
async def cli():
    parser = argparse.ArgumentParser(
        description="Run OpenAI Chat Completion with various structured outputs capabilities",
    )
    _ = parser.add_argument(
        "--constraint",
        type=str,
        nargs="+",
        choices=[*list(PARAMS), "*"],
        default=["*"],
        help="Specify which constraint(s) to run.",
    )
    _ = parser.add_argument(
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable streaming output",
    )
    _ = parser.add_argument(
        "--reasoning",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable printing of reasoning traces if available.",
    )
    args = parser.parse_args()

    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
    client = openai.AsyncOpenAI(base_url=base_url, api_key="EMPTY")
    constraints = list(PARAMS) if "*" in args.constraint else list(set(args.constraint))
    model = (await client.models.list()).data[0].id

    if args.stream:
        results = await asyncio.gather(
            *[
                client.chat.completions.create(
                    model=model,
                    max_tokens=1024,
                    stream=True,
                    **PARAMS[name],
                )
                for name in constraints
            ]
        )
        for constraint, stream in zip(constraints, results):
            await print_stream_response(stream, constraint, args)
    else:
        results = await asyncio.gather(
            *[
                client.chat.completions.create(
                    model=model,
                    max_tokens=1024,
                    stream=False,
                    **PARAMS[name],
                )
                for name in constraints
            ]
        )
        for constraint, response in zip(constraints, results):
            print(f"\n\n{constraint}:")
            message = response.choices[0].message
            if args.reasoning and hasattr(message, "reasoning"):
                print(f"  Reasoning: {message.reasoning or ''}")
            print(f"  Content: {message.content!r}")
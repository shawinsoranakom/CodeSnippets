async def async_main(args: argparse.Namespace) -> None:
    """
    Main function
    """
    print("Initializing...")
    print("Enter `alt+enter` or `escape+enter` to send a message")
    # Read and parse cookies
    cookies = None
    if args.cookie_file:
        cookies = json.loads(open(args.cookie_file, encoding="utf-8").read())
    bot = await Chatbot.create(proxy=args.proxy, cookies=cookies)
    session = _create_session()
    completer = _create_completer(["!help", "!exit", "!reset"])
    initial_prompt = args.prompt

    while True:
        print("\nYou:")
        if initial_prompt:
            question = initial_prompt
            print(question)
            initial_prompt = None
        else:
            question = (
                input()
                if args.enter_once
                else await _get_input_async(session=session, completer=completer)
            )
        print()
        if question == "!exit":
            break
        if question == "!help":
            print(
                """
            !help - Show this help message
            !exit - Exit the program
            !reset - Reset the conversation
            """,
            )
            continue
        if question == "!reset":
            await bot.reset()
            continue
        print("Bot:")
        if args.no_stream:
            print(
                (
                    await bot.ask(
                        prompt=question,
                        conversation_style=args.style,
                        wss_link=args.wss_link,
                    )
                )["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"],
            )
        else:
            wrote = 0
            if args.rich:
                md = Markdown("")
                with Live(md, auto_refresh=False) as live:
                    async for final, response in bot.ask_stream(
                        prompt=question,
                        conversation_style=args.style,
                        wss_link=args.wss_link,
                    ):
                        if not final:
                            if wrote > len(response):
                                print(md)
                                print(Markdown("***Bing revoked the response.***"))
                            wrote = len(response)
                            md = Markdown(response)
                            live.update(md, refresh=True)
            else:
                async for final, response in bot.ask_stream(
                    prompt=question,
                    conversation_style=args.style,
                    wss_link=args.wss_link,
                ):
                    if not final:
                        if not wrote:
                            print(response, end="", flush=True)
                        else:
                            print(response[wrote:], end="", flush=True)
                        wrote = len(response)
                print()
    await bot.close()
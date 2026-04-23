async def run_args(input_val, args):
    try:
        # ensure dirs
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.conversation_file:
            args.conversation_file.parent.mkdir(parents=True, exist_ok=True)
        args.cookies_dir.mkdir(parents=True, exist_ok=True)

        if args.debug:
            debug.logging = True

        conv = ConversationManager(
            None if args.no_config else args.conversation_file,
            model=args.model,
            provider=args.provider,
            max_messages=args.max_messages
        )
        if args.clear_history:
            conv.history = []
            conv.conversation = None

        set_cookies_dir(str(args.cookies_dir))
        read_cookie_files()

        client = ClientFactory.create_async_client(provider=conv.provider)

        if input_val == "models":
            models = client.models.get_all()
            print("\nAvailable models:")
            for m in models:
                print(f"- {m}")
            return

        if isinstance(args.edit, Path):
            file_to_edit = args.edit
            if not file_to_edit.exists():
                print(f"ERROR: file not found: {file_to_edit}", file=sys.stderr)
                sys.exit(1)
            text = file_to_edit.read_text(encoding="utf-8")
            # we will both send and overwrite this file
            input_val = f"```file: {file_to_edit}\n{text}\n```\n" + (input_val[1] if isinstance(input_val, tuple) else input_val)
            output_target = file_to_edit
        else:
            # normal, non-edit mode
            output_target = args.output

        await stream_response(client, input_val, conv, output_target, args.instructions)
        conv.save()

    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)
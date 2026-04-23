def run_client_args(args, exit_on_error=True):
    input_txt = ""
    media = []
    rest = 0

    for idx, tok in enumerate(args.input):
        if tok.startswith(("http://","https://")):
            # same URL logic...
            resp = requests.head(tok, allow_redirects=True)
            if resp.ok and resp.headers.get("Content-Type","").startswith("image"):
                media.append(tok)
            else:
                if not has_markitdown:
                    raise MissingRequirementsError("Install markitdown")
                md = MarkItDown()
                txt = md.convert_url(tok).text_content
                input_txt += f"\n```source: {tok}\n{txt}\n```\n"
        elif os.path.isfile(tok):
            head = Path(tok).read_bytes()[:12]
            try:
                if is_accepted_format(head):
                    media.append(Path(tok))
                    is_img = True
                else:
                    is_img = False
            except ValueError:
                is_img = False
            if not is_img:
                txt = Path(tok).read_text(encoding="utf-8")
                input_txt += f"\n```file: {tok}\n{txt}\n```\n"
        else:
            rest = idx
            break
        rest = idx + 1

    tail = args.input[rest:]
    if tail:
        input_txt = " ".join(tail) + "\n" + input_txt

    if not sys.stdin.isatty() and not input_txt:
        input_txt = sys.stdin.read()

    if media:
        val = (media, input_txt)
    else:
        val = input_txt.strip()

    if exit_on_error and not val:
        print("No input provided. Use -h.", file=sys.stderr)
        sys.exit(1)
    elif not val:
        raise argparse.ArgumentError(None, "No input provided. Use -h for help.")

    asyncio.run(run_args(val, args))
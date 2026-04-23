def run_chat(args: InputArgument = None):
    model_args, data_args, _, sample_args = get_args(args)
    if sample_args.sample_backend != SampleBackend.HF:
        model_args.init_plugin = {"name": "init_on_meta"}

    model_engine = ModelEngine(model_args)
    sampler = SyncSampler(sample_args, model_args, model_engine.model, model_engine.renderer)
    if data_args.train_dataset is not None:
        dataset = DataEngine(data_args.train_dataset)
        sampler.batch_infer(dataset)
    else:
        if os.name != "nt":
            try:
                import readline  # noqa: F401
            except ImportError:
                print("Install `readline` for a better experience.")

        messages = []
        print("Welcome to the CLI application, use `clear` to remove the history, use `exit` to exit the application.")

        while True:
            try:
                query = input("\nUser: ")
            except UnicodeDecodeError:
                print("Detected decoding error at the inputs, please set the terminal encoding to utf-8.")
                continue
            except Exception:
                raise

            if query.strip() == "exit":
                break

            if query.strip() == "clear":
                messages = []
                print("History has been removed.")
                continue

            messages.append({"role": "user", "content": [{"type": "text", "value": query}]})
            print("Assistant: ", end="", flush=True)

            response = ""
            for new_text in sampler.generate(messages):
                print(new_text, end="", flush=True)
                response += new_text

            print()
            messages.append(model_engine.renderer.parse_message(response))
def create_completion(model: str, messages: Messages, stream: bool = False, **kwargs):
        global MODEL_LIST
        if MODEL_LIST is None:
            MODEL_LIST = get_models()
        if model not in MODEL_LIST:
            raise ValueError(f'Model "{model}" not found / not yet implemented')

        model = MODEL_LIST[model]
        model_file = model["path"]
        model_dir = find_model_dir(model_file)
        if not os.path.isfile(os.path.join(model_dir, model_file)):
            print(f'Model file "models/{model_file}" not found.')
            download = input(f"Do you want to download {model_file}? [y/n]: ")
            if download in ["y", "Y"]:
                GPT4All.download_model(model_file, model_dir)
            else:
                raise ValueError(f'Model "{model_file}" not found.')

        model = GPT4All(model_name=model_file,
                        #n_threads=8,
                        verbose=False,
                        allow_download=False,
                        model_path=model_dir)

        system_message = "\n".join(message["content"] for message in messages if message["role"] == "system")
        if system_message:
            system_message = "A chat between a curious user and an artificial intelligence assistant."

        prompt_template = "USER: {0}\nASSISTANT: "
        conversation    = "\n" . join(
            f"{message['role'].upper()}: {message['content']}"
            for message in messages
            if message["role"] != "system"
        ) + "\nASSISTANT: "

        def should_not_stop(token_id: int, token: str):
            return "USER" not in token

        with model.chat_session(system_message, prompt_template):
            if stream:
                for token in model.generate(conversation, streaming=True, callback=should_not_stop):
                    yield token
            else:
                yield model.generate(conversation, callback=should_not_stop)
def download_model(models_dir, models, interpreter):
        # Get RAM and disk information
        total_ram = psutil.virtual_memory().total / (
            1024 * 1024 * 1024
        )  # Convert bytes to GB
        free_disk_space = psutil.disk_usage("/").free / (
            1024 * 1024 * 1024
        )  # Convert bytes to GB

        # Display the users hardware specs
        interpreter.display_message(
            f"Your machine has `{total_ram:.2f}GB` of RAM, and `{free_disk_space:.2f}GB` of free storage space."
        )

        if total_ram < 10:
            interpreter.display_message(
                f"\nYour computer realistically can only run smaller models less than 4GB, Phi-2 might be the best model for your computer.\n"
            )
        elif 10 <= total_ram < 30:
            interpreter.display_message(
                f"\nYour computer could handle a mid-sized model (4-10GB), Mistral-7B might be the best model for your computer.\n"
            )
        else:
            interpreter.display_message(
                f"\nYour computer should have enough RAM to run any model below.\n"
            )

        interpreter.display_message(
            f"In general, the larger the model, the better the performance, but choose a model that best fits your computer's hardware. \nOnly models you have the storage space to download are shown:\n"
        )

        try:
            model_list = [
                {
                    "name": "Llama-3.1-8B-Instruct",
                    "file_name": "Meta-Llama-3-8B-Instruct.Q4_K_M.llamafile",
                    "size": 4.95,
                    "url": "https://huggingface.co/Mozilla/Meta-Llama-3.1-8B-Instruct-llamafile/resolve/main/Meta-Llama-3.1-8B-Instruct.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "Gemma-2-9b",
                    "file_name": "gemma-2-9b-it.Q4_K_M.llamafile",
                    "size": 5.79,
                    "url": "https://huggingface.co/jartine/gemma-2-9b-it-llamafile/resolve/main/gemma-2-9b-it.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "Phi-3-mini",
                    "file_name": "Phi-3-mini-4k-instruct.Q4_K_M.llamafile",
                    "size": 2.42,
                    "url": "https://huggingface.co/Mozilla/Phi-3-mini-4k-instruct-llamafile/resolve/main/Phi-3-mini-4k-instruct.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "Moondream2 (vision)",
                    "file_name": "moondream2-q5km-050824.llamafile",
                    "size": 1.98,
                    "url": "https://huggingface.co/cjpais/moondream2-llamafile/resolve/main/moondream2-q5km-050824.llamafile?download=true",
                },
                {
                    "name": "Mistral-7B-Instruct",
                    "file_name": "Mistral-7B-Instruct-v0.3.Q4_K_M.llamafile",
                    "size": 4.40,
                    "url": "https://huggingface.co/Mozilla/Mistral-7B-Instruct-v0.3-llamafile/resolve/main/Mistral-7B-Instruct-v0.3.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "Gemma-2-27b",
                    "file_name": "gemma-2-27b-it.Q4_K_M.llamafile",
                    "size": 16.7,
                    "url": "https://huggingface.co/jartine/gemma-2-27b-it-llamafile/resolve/main/gemma-2-27b-it.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "TinyLlama-1.1B",
                    "file_name": "TinyLlama-1.1B-Chat-v1.0.Q4_K_M.llamafile",
                    "size": 0.70,
                    "url": "https://huggingface.co/Mozilla/TinyLlama-1.1B-Chat-v1.0-llamafile/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "Rocket-3B",
                    "file_name": "rocket-3b.Q4_K_M.llamafile",
                    "size": 1.74,
                    "url": "https://huggingface.co/Mozilla/rocket-3B-llamafile/resolve/main/rocket-3b.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "LLaVA 1.5 (vision)",
                    "file_name": "llava-v1.5-7b-q4.llamafile",
                    "size": 4.29,
                    "url": "https://huggingface.co/Mozilla/llava-v1.5-7b-llamafile/resolve/main/llava-v1.5-7b-q4.llamafile?download=true",
                },
                {
                    "name": "WizardCoder-Python-13B",
                    "file_name": "wizardcoder-python-13b.llamafile",
                    "size": 7.33,
                    "url": "https://huggingface.co/jartine/wizardcoder-13b-python/resolve/main/wizardcoder-python-13b.llamafile?download=true",
                },
                {
                    "name": "WizardCoder-Python-34B",
                    "file_name": "wizardcoder-python-34b-v1.0.Q4_K_M.llamafile",
                    "size": 20.22,
                    "url": "https://huggingface.co/Mozilla/WizardCoder-Python-34B-V1.0-llamafile/resolve/main/wizardcoder-python-34b-v1.0.Q4_K_M.llamafile?download=true",
                },
                {
                    "name": "Mixtral-8x7B-Instruct",
                    "file_name": "mixtral-8x7b-instruct-v0.1.Q5_K_M.llamafile",
                    "size": 30.03,
                    "url": "https://huggingface.co/jartine/Mixtral-8x7B-Instruct-v0.1-llamafile/resolve/main/mixtral-8x7b-instruct-v0.1.Q5_K_M.llamafile?download=true",
                },
            ]

            # Filter models based on available disk space and RAM
            filtered_models = [
                model
                for model in model_list
                if model["size"] <= free_disk_space and model["file_name"] not in models
            ]
            if filtered_models:
                time.sleep(1)

                # Prompt the user to select a model
                model_choices = [
                    f"{model['name']} ({model['size']:.2f}GB)"
                    for model in filtered_models
                ]
                questions = [
                    inquirer.List(
                        "model",
                        message="Select a model to download:",
                        choices=model_choices,
                    )
                ]
                answers = inquirer.prompt(questions)

                if answers == None:
                    exit()

                # Get the selected model
                selected_model = next(
                    model
                    for model in filtered_models
                    if f"{model['name']} ({model['size']}GB)" == answers["model"]
                )

                # Download the selected model
                model_url = selected_model["url"]
                # Extract the basename and remove query parameters
                filename = os.path.basename(model_url).split("?")[0]
                model_path = os.path.join(models_dir, filename)

                # time.sleep(0.3)

                print(f"\nDownloading {selected_model['name']}...\n")
                wget.download(model_url, model_path)

                # Make the model executable if not on Windows
                if platform.system() != "Windows":
                    subprocess.run(["chmod", "+x", model_path], check=True)

                print(f"\nModel '{selected_model['name']}' downloaded successfully.\n")

                interpreter.display_message(
                    "To view or delete downloaded local models, run `interpreter --local_models`\n\n"
                )

                return model_path
            else:
                print(
                    "\nYour computer does not have enough storage to download any local LLMs.\n"
                )
                return None
        except Exception as e:
            print(e)
            print(
                "\nAn error occurred while trying to download the model. Please try again or use a different local model provider.\n"
            )
            return None
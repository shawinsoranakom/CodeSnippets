def load(self):
        if self._is_loaded:
            return

        if self.model.startswith("ollama/") and not ":" in self.model:
            self.model = self.model + ":latest"

        self._is_loaded = True

        if self.model.startswith("ollama/"):
            model_name = self.model.replace("ollama/", "")
            api_base = getattr(self, "api_base", None) or os.getenv(
                "OLLAMA_HOST", "http://localhost:11434"
            )
            names = []
            try:
                # List out all downloaded ollama models. Will fail if ollama isn't installed
                response = requests.get(f"{api_base}/api/tags")
                if response.ok:
                    data = response.json()
                    names = [
                        model["name"]
                        for model in data["models"]
                        if "name" in model and model["name"]
                    ]

            except Exception as e:
                print(str(e))
                self.interpreter.display_message(
                    f"> Ollama not found\n\nPlease download Ollama from [ollama.com](https://ollama.com/) to use `{model_name}`.\n"
                )
                exit()

            # Download model if not already installed
            if model_name not in names:
                self.interpreter.display_message(f"\nDownloading {model_name}...\n")
                requests.post(f"{api_base}/api/pull", json={"name": model_name})

            # Get context window if not set
            if self.context_window == None:
                response = requests.post(
                    f"{api_base}/api/show", json={"name": model_name}
                )
                model_info = response.json().get("model_info", {})
                context_length = None
                for key in model_info:
                    if "context_length" in key:
                        context_length = model_info[key]
                        break
                if context_length is not None:
                    self.context_window = context_length
            if self.max_tokens == None:
                if self.context_window != None:
                    self.max_tokens = int(self.context_window * 0.2)

            # Send a ping, which will actually load the model
            model_name = model_name.replace(":latest", "")
            print(f"Loading {model_name}...\n")

            old_max_tokens = self.max_tokens
            self.max_tokens = 1
            self.interpreter.computer.ai.chat("ping")
            self.max_tokens = old_max_tokens

            self.interpreter.display_message("*Model loaded.*\n")

        # Validate LLM should be moved here!!

        if self.context_window == None:
            try:
                model_info = litellm.get_model_info(model=self.model)
                self.context_window = model_info["max_input_tokens"]
                if self.max_tokens == None:
                    self.max_tokens = min(
                        int(self.context_window * 0.2), model_info["max_output_tokens"]
                    )
            except:
                pass
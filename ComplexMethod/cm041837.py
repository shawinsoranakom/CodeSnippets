def run(self, messages):
        """
        We're responsible for formatting the call into the llm.completions object,
        starting with LMC messages in interpreter.messages, going to OpenAI compatible messages into the llm,
        respecting whether it's a vision or function model, respecting its context window and max tokens, etc.

        And then processing its output, whether it's a function or non function calling model, into LMC format.
        """

        if not self._is_loaded:
            self.load()

        if (
            self.max_tokens is not None
            and self.context_window is not None
            and self.max_tokens > self.context_window
        ):
            print(
                "Warning: max_tokens is larger than context_window. Setting max_tokens to be 0.2 times the context_window."
            )
            self.max_tokens = int(0.2 * self.context_window)

        # Assertions
        assert (
            messages[0]["role"] == "system"
        ), "First message must have the role 'system'"
        for msg in messages[1:]:
            assert (
                msg["role"] != "system"
            ), "No message after the first can have the role 'system'"

        model = self.model
        if model in [
            "claude-3.5",
            "claude-3-5",
            "claude-3.5-sonnet",
            "claude-3-5-sonnet",
        ]:
            model = "claude-3-5-sonnet-20240620"
            self.model = "claude-3-5-sonnet-20240620"
        # Setup our model endpoint
        if model == "i":
            model = "openai/i"
            if not hasattr(self.interpreter, "conversation_id"):  # Only do this once
                self.context_window = 7000
                self.api_key = "x"
                self.max_tokens = 1000
                self.api_base = "https://api.openinterpreter.com/v0"
                self.interpreter.conversation_id = str(uuid.uuid4())

        # Detect function support
        if self.supports_functions == None:
            try:
                if litellm.supports_function_calling(model):
                    self.supports_functions = True
                else:
                    self.supports_functions = False
            except:
                self.supports_functions = False

        # Detect vision support
        if self.supports_vision == None:
            try:
                if litellm.supports_vision(model):
                    self.supports_vision = True
                else:
                    self.supports_vision = False
            except:
                self.supports_vision = False

        # Trim image messages if they're there
        image_messages = [msg for msg in messages if msg["type"] == "image"]
        if self.supports_vision:
            if self.interpreter.os:
                # Keep only the last two images if the interpreter is running in OS mode
                if len(image_messages) > 1:
                    for img_msg in image_messages[:-2]:
                        messages.remove(img_msg)
                        if self.interpreter.verbose:
                            print("Removing image message!")
            else:
                # Delete all the middle ones (leave only the first and last 2 images) from messages_for_llm
                if len(image_messages) > 3:
                    for img_msg in image_messages[1:-2]:
                        messages.remove(img_msg)
                        if self.interpreter.verbose:
                            print("Removing image message!")
                # Idea: we could set detail: low for the middle messages, instead of deleting them
        elif self.supports_vision == False and self.vision_renderer:
            for img_msg in image_messages:
                if img_msg["format"] != "description":
                    self.interpreter.display_message("\n  *Viewing image...*\n")

                    if img_msg["format"] == "path":
                        precursor = f"The image I'm referring to ({img_msg['content']}) contains the following: "
                        if self.interpreter.computer.import_computer_api:
                            postcursor = f"\nIf you want to ask questions about the image, run `computer.vision.query(path='{img_msg['content']}', query='(ask any question here)')` and a vision AI will answer it."
                        else:
                            postcursor = ""
                    else:
                        precursor = "Imagine I have just shown you an image with this description: "
                        postcursor = ""

                    try:
                        image_description = self.vision_renderer(lmc=img_msg)
                        ocr = self.interpreter.computer.vision.ocr(lmc=img_msg)

                        # It would be nice to format this as a message to the user and display it like: "I see: image_description"

                        img_msg["content"] = (
                            precursor
                            + image_description
                            + "\n---\nI've OCR'd the image, this is the result (this may or may not be relevant. If it's not relevant, ignore this): '''\n"
                            + ocr
                            + "\n'''"
                            + postcursor
                        )
                        img_msg["format"] = "description"

                    except ImportError:
                        print(
                            "\nTo use local vision, run `pip install 'open-interpreter[local]'`.\n"
                        )
                        img_msg["format"] = "description"
                        img_msg["content"] = ""

        # Convert to OpenAI messages format
        messages = convert_to_openai_messages(
            messages,
            function_calling=self.supports_functions,
            vision=self.supports_vision,
            shrink_images=self.interpreter.shrink_images,
            interpreter=self.interpreter,
        )

        system_message = messages[0]["content"]
        messages = messages[1:]

        # Trim messages
        try:
            if self.context_window and self.max_tokens:
                trim_to_be_this_many_tokens = (
                    self.context_window - self.max_tokens - 25
                )  # arbitrary buffer
                messages = tt.trim(
                    messages,
                    system_message=system_message,
                    max_tokens=trim_to_be_this_many_tokens,
                )
            elif self.context_window and not self.max_tokens:
                # Just trim to the context window if max_tokens not set
                messages = tt.trim(
                    messages,
                    system_message=system_message,
                    max_tokens=self.context_window,
                )
            else:
                try:
                    messages = tt.trim(
                        messages, system_message=system_message, model=model
                    )
                except:
                    if len(messages) == 1:
                        if self.interpreter.in_terminal_interface:
                            self.interpreter.display_message(
                                """
**We were unable to determine the context window of this model.** Defaulting to 8000.

If your model can handle more, run `interpreter --context_window {token limit} --max_tokens {max tokens per response}`.

Continuing...
                            """
                            )
                        else:
                            self.interpreter.display_message(
                                """
**We were unable to determine the context window of this model.** Defaulting to 8000.

If your model can handle more, run `self.context_window = {token limit}`.

Also please set `self.max_tokens = {max tokens per response}`.

Continuing...
                            """
                            )
                    messages = tt.trim(
                        messages, system_message=system_message, max_tokens=8000
                    )
        except:
            # If we're trimming messages, this won't work.
            # If we're trimming from a model we don't know, this won't work.
            # Better not to fail until `messages` is too big, just for frustrations sake, I suppose.

            # Reunite system message with messages
            messages = [{"role": "system", "content": system_message}] + messages

            pass

        # If there should be a system message, there should be a system message!
        # Empty system messages appear to be deleted :(
        if system_message == "":
            if messages[0]["role"] != "system":
                messages = [{"role": "system", "content": system_message}] + messages

        ## Start forming the request

        params = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        # Optional inputs
        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base
        if self.api_version:
            params["api_version"] = self.api_version
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        if self.temperature:
            params["temperature"] = self.temperature
        if hasattr(self.interpreter, "conversation_id"):
            params["conversation_id"] = self.interpreter.conversation_id

        # Set some params directly on LiteLLM
        if self.max_budget:
            litellm.max_budget = self.max_budget
        if self.interpreter.verbose:
            litellm.set_verbose = True

        if (
            self.interpreter.debug == True and False  # DISABLED
        ):  # debug will equal "server" if we're debugging the server specifically
            print("\n\n\nOPENAI COMPATIBLE MESSAGES:\n\n\n")
            for message in messages:
                if len(str(message)) > 5000:
                    print(str(message)[:200] + "...")
                else:
                    print(message)
                print("\n")
            print("\n\n\n")

        if self.supports_functions:
            # yield from run_function_calling_llm(self, params)
            yield from run_tool_calling_llm(self, params)
        else:
            yield from run_text_llm(self, params)
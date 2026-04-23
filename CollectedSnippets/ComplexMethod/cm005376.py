async def _inner_run(self):
        interface = RichInterface(model_id=self.model_id, user_id=self.user, base_url=self.base_url)
        interface.clear()
        chat = new_chat_history(self.system_prompt)

        # Starts the session with a minimal help message at the top, so that a user doesn't get stuck
        interface.print_help(minimal=True)
        interface.print_model_load(self.model_id)

        config = self.config

        async with AsyncInferenceClient(base_url=self.base_url) as client:
            pending_user_input: str | None = None
            while True:
                try:
                    if pending_user_input is not None:
                        user_input = pending_user_input
                        pending_user_input = None
                        interface.print_user_message(user_input)
                    else:
                        user_input = interface.input()

                    # User commands
                    if user_input == "!exit":
                        break

                    elif user_input == "!clear":
                        chat = new_chat_history(self.system_prompt)
                        interface.clear()
                        continue

                    elif user_input == "!help":
                        interface.print_help()
                        continue

                    elif user_input.startswith("!save") and len(user_input.split()) < 2:
                        split_input = user_input.split()
                        filename = (
                            split_input[1]
                            if len(split_input) == 2
                            else os.path.join(
                                self.save_folder, self.model_id, f"chat_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                            )
                        )
                        save_chat(filename=filename, chat=chat, settings=self.settings)
                        interface.print_color(text=f"Chat saved to {filename}!", color="green")
                        continue

                    elif user_input.startswith("!set"):
                        # splits the new args into a list of strings, each string being a `flag=value` pair (same format as
                        # `generate_flags`)
                        new_generate_flags = user_input[4:].strip()
                        new_generate_flags = new_generate_flags.split()
                        # sanity check: each member in the list must have an =
                        for flag in new_generate_flags:
                            if "=" not in flag:
                                interface.print_color(
                                    text=(
                                        f"Invalid flag format, missing `=` after `{flag}`. Please use the format "
                                        "`arg_1=value_1 arg_2=value_2 ...`."
                                    ),
                                    color="red",
                                )
                                break
                        else:
                            # Update config from user flags
                            config.update(**parse_generate_flags(new_generate_flags))
                        continue

                    elif user_input.startswith("!example") and len(user_input.split()) == 2:
                        example_name = user_input.split()[1]
                        if example_name in self.examples:
                            interface.clear()
                            chat = []
                            interface.print_user_message(self.examples[example_name]["text"])
                            chat.append({"role": "user", "content": self.examples[example_name]["text"]})
                        else:
                            example_error = f"Example {example_name} not found in list of available examples: {list(self.examples.keys())}."
                            interface.print_color(text=example_error, color="red")

                    elif user_input == "!status":
                        interface.print_status(config=config)
                        continue

                    elif user_input.startswith("!"):
                        interface.print_color(
                            text=f"'{user_input}' is not a valid command. Showing help message.", color="red"
                        )
                        interface.print_help()
                        continue

                    else:
                        chat.append({"role": "user", "content": user_input})

                    extra_body = {
                        "generation_config": config.to_json_string(),
                        "model": self.model_id,
                    }

                    stream = client.chat_completion(
                        chat,
                        stream=True,
                        model=self.model_id,
                        extra_body=extra_body,
                    )

                    model_output, finish_reason = await interface.stream_output(stream)

                    chat.append({"role": "assistant", "content": model_output})

                    if finish_reason == "length":
                        interface.print_color("Generation stopped after reaching the token limit.", "yellow")
                        if interface.confirm("Continue generating?"):
                            pending_user_input = "Please continue. Do not repeat text.”"
                            continue
                except KeyboardInterrupt:
                    break
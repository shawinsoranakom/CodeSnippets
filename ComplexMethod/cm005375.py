def handle_non_exit_user_commands(
        self,
        user_input: str,
        interface: RichInterface,
        examples: dict[str, dict[str, str]],
        config: GenerationConfig,
        chat: list[dict],
    ) -> tuple[list[dict], GenerationConfig]:
        """
        Handles all user commands except for `!exit`. May update the chat history (e.g. reset it) or the
        generation config (e.g. set a new flag).
        """
        valid_command = True

        if user_input == "!clear":
            chat = new_chat_history(self.system_prompt)
            interface.clear()

        elif user_input == "!help":
            interface.print_help()

        elif user_input.startswith("!save") and len(user_input.split()) < 2:
            split_input = user_input.split()
            filename = (
                split_input[1]
                if len(split_input) == 2
                else os.path.join(self.save_folder, self.model_id, f"chat_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json")
            )
            save_chat(filename=filename, chat=chat, settings=self.settings)
            interface.print_color(text=f"Chat saved to {filename}!", color="green")

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

        elif user_input.startswith("!example") and len(user_input.split()) == 2:
            example_name = user_input.split()[1]
            if example_name in examples:
                interface.clear()
                chat = []
                interface.print_user_message(examples[example_name]["text"])
                chat.append({"role": "user", "content": examples[example_name]["text"]})
            else:
                example_error = (
                    f"Example {example_name} not found in list of available examples: {list(examples.keys())}."
                )
                interface.print_color(text=example_error, color="red")

        elif user_input == "!status":
            interface.print_status(config=config)

        else:
            valid_command = False
            interface.print_color(text=f"'{user_input}' is not a valid command. Showing help message.", color="red")
            interface.print_help()

        return chat, valid_command, config
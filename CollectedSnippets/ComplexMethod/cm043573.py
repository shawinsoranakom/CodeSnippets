def get_completions(  # noqa: PLR0912
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get completions."""
        # Split document.
        cmd = ""
        text = document.text_before_cursor.lstrip()
        if " " in text:
            cmd = text.split(" ")[0]
        if "-" in text:
            if text.rfind("--") == -1 or text.rfind("-") - 1 > text.rfind("--"):
                unprocessed_text = "-" + text.split("-")[-1]
            else:
                unprocessed_text = "--" + text.split("--")[-1]
        else:
            unprocessed_text = text
        stripped_len = len(document.text_before_cursor) - len(text)

        # Check if there are multiple flags for the same command
        if self.complementary:
            for same_flags in self.complementary:
                if (
                    same_flags[0] in self.flags_processed
                    and same_flags[1] not in self.flags_processed
                ) or (
                    same_flags[1] in self.flags_processed
                    and same_flags[0] not in self.flags_processed
                ):
                    if same_flags[0] in self.flags_processed:
                        self.flags_processed.append(same_flags[1])
                    elif same_flags[1] in self.flags_processed:
                        self.flags_processed.append(same_flags[0])

                    if cmd:
                        self.options = {
                            k: self.original_options.get(cmd).options[k]  # type: ignore
                            for k in self.original_options.get(cmd).options  # type: ignore
                            if k not in self.flags_processed
                        }
                    else:
                        self.options = {
                            k: self.original_options[k]
                            for k in self.original_options
                            if k not in self.flags_processed
                        }

        # If there is a space, check for the first term, and use a subcompleter.
        if " " in unprocessed_text:
            first_term = unprocessed_text.split()[0]

            # user is updating one of the values
            if unprocessed_text[-1] != " ":
                self.flags_processed = [
                    flag for flag in self.flags_processed if flag != first_term
                ]

                if self.complementary:
                    for same_flags in self.complementary:
                        if (
                            same_flags[0] in self.flags_processed
                            and same_flags[1] not in self.flags_processed
                        ) or (
                            same_flags[1] in self.flags_processed
                            and same_flags[0] not in self.flags_processed
                        ):
                            if same_flags[0] in self.flags_processed:
                                self.flags_processed.remove(same_flags[0])
                            elif same_flags[1] in self.flags_processed:
                                self.flags_processed.remove(same_flags[1])

                if cmd and self.original_options.get(cmd):
                    self.options = self.original_options
                else:
                    self.options = {
                        k: self.original_options[k]
                        for k in self.original_options
                        if k not in self.flags_processed
                    }

            if "-" not in text:
                completer = self.options.get(first_term)
            elif cmd in self.options and self.options.get(cmd):
                completer = self.options.get(cmd).options.get(first_term)  # type: ignore
            else:
                completer = self.options.get(first_term)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = unprocessed_text[len(first_term) :].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                # Provides auto-completion but if user doesn't take it still keep going
                if " " in new_document.text:
                    if (
                        new_document.text in [f"{opt} " for opt in self.options]
                        or unprocessed_text[-1] == " "
                    ):
                        self.flags_processed.append(first_term)
                        if cmd:
                            self.options = {
                                k: self.original_options.get(cmd).options[k]  # type: ignore
                                for k in self.original_options.get(cmd).options  # type: ignore
                                if k not in self.flags_processed
                            }
                        else:
                            self.options = {
                                k: self.original_options[k]
                                for k in self.original_options
                                if k not in self.flags_processed
                            }

                # In case the users inputs a single boolean flag
                elif not completer.options:  # type: ignore
                    self.flags_processed.append(first_term)

                    if self.complementary:
                        for same_flags in self.complementary:
                            if (
                                same_flags[0] in self.flags_processed
                                and same_flags[1] not in self.flags_processed
                            ) or (
                                same_flags[1] in self.flags_processed
                                and same_flags[0] not in self.flags_processed
                            ):
                                if same_flags[0] in self.flags_processed:
                                    self.flags_processed.append(same_flags[1])
                                elif same_flags[1] in self.flags_processed:
                                    self.flags_processed.append(same_flags[0])

                    if cmd:
                        self.options = {
                            k: self.original_options.get(cmd).options[k]  # type: ignore
                            for k in self.original_options.get(cmd).options  # type: ignore
                            if k not in self.flags_processed
                        }
                    else:
                        self.options = {
                            k: self.original_options[k]
                            for k in self.original_options
                            if k not in self.flags_processed
                        }

                else:
                    # This is a NestedCompleter
                    yield from completer.get_completions(new_document, complete_event)

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            # check if the prompt has been updated in the meantime
            if " " in text or "-" in text:
                actual_flags_processed = [
                    flag for flag in self.flags_processed if flag in text
                ]

                if self.complementary:
                    for same_flags in self.complementary:
                        if (
                            same_flags[0] in actual_flags_processed
                            and same_flags[1] not in actual_flags_processed
                        ) or (
                            same_flags[1] in actual_flags_processed
                            and same_flags[0] not in actual_flags_processed
                        ):
                            if same_flags[0] in actual_flags_processed:
                                actual_flags_processed.append(same_flags[1])
                            elif same_flags[1] in actual_flags_processed:
                                actual_flags_processed.append(same_flags[0])

                if len(actual_flags_processed) < len(self.flags_processed):
                    self.flags_processed = actual_flags_processed
                    if cmd:
                        self.options = {
                            k: self.original_options.get(cmd).options[k]  # type: ignore
                            for k in self.original_options.get(cmd).options  # type: ignore
                            if k not in self.flags_processed
                        }
                    else:
                        self.options = {
                            k: self.original_options[k]
                            for k in self.original_options
                            if k not in self.flags_processed
                        }

            command = self.options.get(cmd)
            options = command.options if command else {}  # type: ignore
            command_options = [f"{cmd} {opt}" for opt in options]
            text_list = [text in val for val in command_options]
            if cmd and cmd in self.options and text_list:
                completer = WordCompleter(
                    list(self.options.get(cmd).options.keys()),  # type: ignore
                    ignore_case=self.ignore_case,
                )
            elif bool([val for val in self.options if text in val]):
                completer = WordCompleter(
                    list(self.options.keys()), ignore_case=self.ignore_case
                )
            else:
                # The user has delete part of the first command and we need to reset options
                if bool([val for val in self.original_options if text in val]):
                    self.options = self.original_options
                    self.flags_processed = list()
                completer = WordCompleter(
                    list(self.options.keys()), ignore_case=self.ignore_case
                )

            # This is a WordCompleter
            yield from completer.get_completions(document, complete_event)
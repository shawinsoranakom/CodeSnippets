def _respond_and_store(self):
        """
        Pulls from the respond stream, adding delimiters. Some things, like active_line, console, confirmation... these act specially.
        Also assembles new messages and adds them to `self.messages`.
        """
        self.verbose = False

        # Utility function
        def is_ephemeral(chunk):
            """
            Ephemeral = this chunk doesn't contribute to a message we want to save.
            """
            if "format" in chunk and chunk["format"] == "active_line":
                return True
            if chunk["type"] == "review":
                return True
            return False

        last_flag_base = None

        try:
            for chunk in respond(self):
                # For async usage
                if hasattr(self, "stop_event") and self.stop_event.is_set():
                    print("Open Interpreter stopping.")
                    break

                if chunk["content"] == "":
                    continue

                # If active_line is None, we finished running code.
                if (
                    chunk.get("format") == "active_line"
                    and chunk.get("content", "") == None
                ):
                    # If output wasn't yet produced, add an empty output
                    if self.messages[-1]["role"] != "computer":
                        self.messages.append(
                            {
                                "role": "computer",
                                "type": "console",
                                "format": "output",
                                "content": "",
                            }
                        )

                # Handle the special "confirmation" chunk, which neither triggers a flag or creates a message
                if chunk["type"] == "confirmation":
                    # Emit a end flag for the last message type, and reset last_flag_base
                    if last_flag_base:
                        yield {**last_flag_base, "end": True}
                        last_flag_base = None

                    if self.auto_run == False:
                        yield chunk

                    # We want to append this now, so even if content is never filled, we know that the execution didn't produce output.
                    # ... rethink this though.
                    # self.messages.append(
                    #     {
                    #         "role": "computer",
                    #         "type": "console",
                    #         "format": "output",
                    #         "content": "",
                    #     }
                    # )
                    continue

                # Check if the chunk's role, type, and format (if present) match the last_flag_base
                if (
                    last_flag_base
                    and "role" in chunk
                    and "type" in chunk
                    and last_flag_base["role"] == chunk["role"]
                    and last_flag_base["type"] == chunk["type"]
                    and (
                        "format" not in last_flag_base
                        or (
                            "format" in chunk
                            and chunk["format"] == last_flag_base["format"]
                        )
                    )
                ):
                    # If they match, append the chunk's content to the current message's content
                    # (Except active_line, which shouldn't be stored)
                    if not is_ephemeral(chunk):
                        if any(
                            [
                                (property in self.messages[-1])
                                and (
                                    self.messages[-1].get(property)
                                    != chunk.get(property)
                                )
                                for property in ["role", "type", "format"]
                            ]
                        ):
                            self.messages.append(chunk)
                        else:
                            self.messages[-1]["content"] += chunk["content"]
                else:
                    # If they don't match, yield a end message for the last message type and a start message for the new one
                    if last_flag_base:
                        yield {**last_flag_base, "end": True}

                    last_flag_base = {"role": chunk["role"], "type": chunk["type"]}

                    # Don't add format to type: "console" flags, to accommodate active_line AND output formats
                    if "format" in chunk and chunk["type"] != "console":
                        last_flag_base["format"] = chunk["format"]

                    yield {**last_flag_base, "start": True}

                    # Add the chunk as a new message
                    if not is_ephemeral(chunk):
                        self.messages.append(chunk)

                # Yield the chunk itself
                yield chunk

                # Truncate output if it's console output
                if chunk["type"] == "console" and chunk["format"] == "output":
                    self.messages[-1]["content"] = truncate_output(
                        self.messages[-1]["content"],
                        self.max_output,
                        add_scrollbars=self.computer.import_computer_api,  # I consider scrollbars to be a computer API thing
                    )

            # Yield a final end flag
            if last_flag_base:
                yield {**last_flag_base, "end": True}
        except GeneratorExit:
            raise
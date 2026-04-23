def extract_tool_calls_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
        request: ChatCompletionRequest,
    ) -> DeltaMessage | None:
        if not current_text.startswith("[") and not current_text.startswith(
            "<|python_start|>"
        ):
            return DeltaMessage(content=delta_text)

        try:
            # remove <|python_start|> and <|python_end|>
            if current_text.startswith("<|python_start|>"):
                current_text = current_text[len("<|python_start|>") :]
            if current_text.endswith("<|python_end|>"):
                current_text = current_text[: current_text.rfind("<|python_end|>")]
            valid_and_added_text = make_valid_python(current_text)
            if valid_and_added_text is None:
                return None
            valid_text, added_text = valid_and_added_text

            module = ast.parse(valid_text)
            parsed = getattr(module.body[0], "value", None)
            if not isinstance(parsed, ast.List) or not all(
                isinstance(e, ast.Call) for e in parsed.elts
            ):
                raise UnexpectedAstError("Tool output must be a list of function calls")
            tool_calls = [
                handle_single_tool(e)  # type: ignore
                for e in parsed.elts
            ]

            tool_deltas = []
            for index, new_call in enumerate(tool_calls):
                if index < self.current_tool_index:
                    continue

                self.current_tool_index = index
                if len(self.streamed_args_for_tool) == index:
                    self.streamed_args_for_tool.append("")

                new_call_complete = (
                    index < len(tool_calls) - 1 or ")]" not in added_text
                )
                if new_call_complete:
                    self.current_tool_index += 1

                withheld_suffix = added_text[:-2] if not new_call_complete else ""
                if not new_call_complete and added_text[-2] == ")":
                    # Function call is incomplete. Withhold the closing bracket.
                    withheld_suffix = withheld_suffix + "}"
                # Strings get single quotes in the model-produced string.
                # JSON requires double quotes.
                withheld_suffix = withheld_suffix.replace("'", '"')
                delta = compute_tool_delta(
                    self.streamed_args_for_tool[index], new_call, index, withheld_suffix
                )

                if delta is not None:
                    tool_deltas.append(delta)
                    if (
                        delta.function is not None
                        and delta.function.arguments is not None
                    ):
                        self.streamed_args_for_tool[index] += delta.function.arguments

            # HACK: serving_chat.py inspects the internal state of tool parsers
            # when determining its final streaming delta, automatically
            # adding autocompleted JSON.
            # These two lines avoid that nonsense while ensuring finish_reason
            # is set to tool_calls when at least one tool is called.
            if tool_deltas and not self.prev_tool_call_arr:
                self.prev_tool_call_arr = [{"arguments": {}}]

            if tool_deltas:
                return DeltaMessage(tool_calls=tool_deltas)
            elif not added_text and self.current_tool_id > 0:
                # Return an empty DeltaMessage once the tool calls are all done
                # so that finish_reason gets set.
                return DeltaMessage(content="")
            else:
                return None
        except Exception:
            logger.exception("Error trying to handle streaming tool call.")
            logger.debug(
                "Skipping chunk as a result of tool streaming extraction error"
            )
            return None
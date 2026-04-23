async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool | type[BaseModel]] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
        tool_choice: Tool | Literal["auto", "required", "none"] = "auto",
    ) -> CreateResult:
        current_messages: List[Mapping[str, Any]] = [msg.model_dump() for msg in messages]
        if self.mode == "record":
            response = await self.base_client.create(
                messages,
                tools=tools,
                json_output=json_output,
                tool_choice=tool_choice,
                extra_create_args=extra_create_args,
                cancellation_token=cancellation_token,
            )

            rec: RecordDict = {
                "mode": "create",
                "messages": current_messages,
                "response": response.model_dump(),
                "stream": [],
            }
            self.records.append(rec)
            return response
        elif self.mode == "replay":
            if self._record_index >= len(self.records):
                error_str = "\nNo more recorded turns to check."
                self.logger.error(error_str)
                raise ValueError(error_str)
            rec = self.records[self._record_index]
            if rec.get("mode") != "create":
                error_str = f"\nRecorded call type mismatch at index {self._record_index}: expected 'create', got '{rec.get('mode')}'."
                self.logger.error(error_str)
                raise ValueError(error_str)
            recorded_messages = rec.get("messages")
            if recorded_messages != current_messages:
                error_str = (
                    "\nCurrent message list doesn't match the recorded message list. See the pagelogs for details."
                )
                assert recorded_messages is not None
                self.logger.log_dict_list(recorded_messages, "recorded message list")
                assert current_messages is not None
                self.logger.log_dict_list(current_messages, "current message list")
                self.logger.error(error_str)
                raise ValueError(error_str)
            self._record_index += 1
            self._num_checked_records += 1

            data = rec.get("response")
            # Populate a CreateResult from the data.
            assert data is not None
            result = CreateResult(
                content=data.get("content", ""),
                finish_reason=data.get("finish_reason", "stop"),
                usage=data.get("usage", RequestUsage(prompt_tokens=0, completion_tokens=0)),
                cached=True,
            )
            return result

        else:
            error_str = f"\nUnknown mode: {self.mode}"
            self.logger.error(error_str)
            raise ValueError(error_str)
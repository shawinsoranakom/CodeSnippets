async def _aget_response(self, run: Any) -> Any:
        # TODO: Pagination

        if run.status == "completed":
            import openai

            major_version = int(openai.version.VERSION.split(".")[0])
            minor_version = int(openai.version.VERSION.split(".")[1])
            version_gte_1_14 = (major_version > 1) or (
                major_version == 1 and minor_version >= 14  # noqa: PLR2004
            )

            messages = await self.async_client.beta.threads.messages.list(
                run.thread_id,
                order="asc",
            )
            new_messages = [msg for msg in messages if msg.run_id == run.id]
            if not self.as_agent:
                return new_messages
            answer: Any = [
                msg_content for msg in new_messages for msg_content in msg.content
            ]
            if all(
                (
                    isinstance(content, openai.types.beta.threads.TextContentBlock)
                    if version_gte_1_14
                    else isinstance(
                        content,
                        openai.types.beta.threads.MessageContentText,  # type: ignore[attr-defined,unused-ignore]
                    )
                )
                for content in answer
            ):
                answer = "\n".join(content.text.value for content in answer)
            return OpenAIAssistantFinish(
                return_values={
                    "output": answer,
                    "thread_id": run.thread_id,
                    "run_id": run.id,
                },
                log="",
                run_id=run.id,
                thread_id=run.thread_id,
            )
        if run.status == "requires_action":
            if not self.as_agent:
                return run.required_action.submit_tool_outputs.tool_calls
            actions = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                function = tool_call.function
                try:
                    args = json.loads(function.arguments, strict=False)
                except JSONDecodeError as e:
                    msg = (
                        f"Received invalid JSON function arguments: "
                        f"{function.arguments} for function {function.name}"
                    )
                    raise ValueError(msg) from e
                if len(args) == 1 and "__arg1" in args:
                    args = args["__arg1"]
                actions.append(
                    OpenAIAssistantAction(
                        tool=function.name,
                        tool_input=args,
                        tool_call_id=tool_call.id,
                        log="",
                        run_id=run.id,
                        thread_id=run.thread_id,
                    ),
                )
            return actions
        run_info = json.dumps(run.dict(), indent=2)
        msg = f"Unexpected run status: {run.status}. Full run info:\n\n{run_info}"
        raise ValueError(msg)
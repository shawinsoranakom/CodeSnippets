def stream(
        self,
        chatbot: list[dict[str, str]],
        messages: list[dict[str, str]],
        lang: str,
        system: str,
        tools: str,
        image: Any | None,
        video: Any | None,
        audio: Any | None,
        max_new_tokens: int,
        top_p: float,
        temperature: float,
        skip_special_tokens: bool,
        escape_html: bool,
        enable_thinking: bool,
    ) -> Generator[tuple[list[dict[str, str]], list[dict[str, str]]], None, None]:
        r"""Generate output text in stream.

        Inputs: infer.chatbot, infer.messages, infer.system, infer.tools, infer.image, infer.video, ...
        Output: infer.chatbot, infer.messages
        """
        with update_attr(self.engine.template, "enable_thinking", enable_thinking):
            chatbot.append({"role": "assistant", "content": ""})
            response = ""
            for new_text in self.stream_chat(
                messages,
                system,
                tools,
                images=[image] if image else None,
                videos=[video] if video else None,
                audios=[audio] if audio else None,
                max_new_tokens=max_new_tokens,
                top_p=top_p,
                temperature=temperature,
                skip_special_tokens=skip_special_tokens,
            ):
                response += new_text
                if tools:
                    result = self.engine.template.extract_tool(response)
                else:
                    result = response

                if isinstance(result, list):
                    tool_calls = [{"name": tool.name, "arguments": json.loads(tool.arguments)} for tool in result]
                    tool_calls = json.dumps(tool_calls, ensure_ascii=False)
                    output_messages = messages + [{"role": Role.FUNCTION.value, "content": tool_calls}]
                    bot_text = "```json\n" + tool_calls + "\n```"
                else:
                    output_messages = messages + [{"role": Role.ASSISTANT.value, "content": result}]
                    bot_text = _format_response(result, lang, escape_html, self.engine.template.thought_words)

                chatbot[-1] = {"role": "assistant", "content": bot_text}
                yield chatbot, output_messages
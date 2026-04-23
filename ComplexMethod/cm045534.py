async def _invoke_bedrock_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[dict]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        **kwargs,
    ) -> OpenAIResponse:
        # Streaming invocation of Bedrock model
        (
            system_prompt,
            bedrock_messages,
        ) = self._convert_openai_messages_to_bedrock_format(messages)
        response = self.client.converse_stream(
            modelId=model,
            system=system_prompt,
            messages=bedrock_messages,
            inferenceConfig={"temperature": temperature, "maxTokens": max_tokens},
            toolConfig={"tools": tools} if tools else None,
        )

        # Initialize response structure
        bedrock_response = {
            "output": {"message": {"role": "", "content": []}},
            "stopReason": "",
            "usage": {},
            "metrics": {},
        }
        bedrock_response_text = ""
        bedrock_response_tool_input = ""

        # Process streaming response
        stream = response.get("stream")
        if stream:
            for event in stream:
                if event.get("messageStart", {}).get("role"):
                    bedrock_response["output"]["message"]["role"] = event[
                        "messageStart"
                    ]["role"]
                if event.get("contentBlockDelta", {}).get("delta", {}).get("text"):
                    bedrock_response_text += event["contentBlockDelta"]["delta"]["text"]
                    print(
                        event["contentBlockDelta"]["delta"]["text"], end="", flush=True
                    )
                if event.get("contentBlockStop", {}).get("contentBlockIndex") == 0:
                    bedrock_response["output"]["message"]["content"].append(
                        {"text": bedrock_response_text}
                    )
                if event.get("contentBlockStart", {}).get("start", {}).get("toolUse"):
                    bedrock_tool_use = event["contentBlockStart"]["start"]["toolUse"]
                    tool_use = {
                        "toolUseId": bedrock_tool_use["toolUseId"],
                        "name": bedrock_tool_use["name"],
                    }
                    bedrock_response["output"]["message"]["content"].append(
                        {"toolUse": tool_use}
                    )
                    global CURRENT_TOOLUSE_ID
                    CURRENT_TOOLUSE_ID = bedrock_tool_use["toolUseId"]
                if event.get("contentBlockDelta", {}).get("delta", {}).get("toolUse"):
                    bedrock_response_tool_input += event["contentBlockDelta"]["delta"][
                        "toolUse"
                    ]["input"]
                    print(
                        event["contentBlockDelta"]["delta"]["toolUse"]["input"],
                        end="",
                        flush=True,
                    )
                if event.get("contentBlockStop", {}).get("contentBlockIndex") == 1:
                    bedrock_response["output"]["message"]["content"][1]["toolUse"][
                        "input"
                    ] = json.loads(bedrock_response_tool_input)
        print()
        openai_response = self._convert_bedrock_response_to_openai_format(
            bedrock_response
        )
        return openai_response
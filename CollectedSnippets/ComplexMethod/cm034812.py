def process_bucket_tool(messages: Messages, tool: dict) -> Messages:
        """Process bucket tool requests"""
        messages = messages.copy()

        def on_bucket(match):
            return "".join(read_bucket(get_bucket_dir(match.group(1))))

        has_bucket = False
        for message in messages:
            if "content" in message and isinstance(message["content"], str):
                new_message_content = re.sub(
                    r'{"bucket_id":\s*"([^"]*)"}', on_bucket, message["content"]
                )
                if new_message_content != message["content"]:
                    has_bucket = True
                    message["content"] = new_message_content

        last_message_content = messages[-1]["content"]
        if has_bucket and isinstance(last_message_content, str):
            if "\nSource: " in last_message_content:
                messages[-1]["content"] = last_message_content + BUCKET_INSTRUCTIONS

        return messages
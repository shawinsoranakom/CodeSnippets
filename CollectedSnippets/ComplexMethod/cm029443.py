def format_prompt_summary(prompt_messages: List[ChatCompletionMessageParam], truncate: bool = True) -> str:
    parts: list[str] = []
    for message in prompt_messages:
        role = message["role"]
        content = message.get("content")
        text = ""
        image_count = 0

        if isinstance(content, list):
            for item in content:
                if item["type"] == "text":
                    text += item["text"] + " "
                elif item["type"] == "image_url":
                    image_count += 1
        else:
            text = str(content)

        text = text.strip()
        if truncate and len(text) > 40:
            text = text[:40] + "..."

        img_part = f" + [{image_count} images]" if image_count else ""
        parts.append(f"  {role.upper()}: {text}{img_part}")

    return "\n".join(parts)
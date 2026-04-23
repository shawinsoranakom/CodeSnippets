def format_prompt_max_length(messages: Messages, max_lenght: int) -> str:
    prompt = format_prompt(messages)
    start = len(prompt)
    if start > max_lenght:
        if len(messages) > 6:
            prompt = format_prompt(messages[:3] + messages[-3:])
        if len(prompt) > max_lenght:
            if len(messages) > 2:
                prompt = format_prompt([m for m in messages if m["role"] == "system"] + messages[-1:])
            if len(prompt) > max_lenght:
                prompt = messages[-1]["content"]
        debug.log(f"Messages trimmed from: {start} to: {len(prompt)}")
    return prompt
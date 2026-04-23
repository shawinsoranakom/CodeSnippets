def main():
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
    )

    models = client.models.list()
    model = models.data[0].id

    # ruff: noqa: E501
    # For granite: add: `extra_body={"chat_template_kwargs": {"thinking": True}}`
    stream = client.chat.completions.create(model=model, messages=messages, stream=True)

    print("client: Start streaming chat completions...")
    printed_reasoning = False
    printed_content = False

    for chunk in stream:
        # Safely extract reasoning and content from delta,
        # defaulting to None if attributes don't exist or are empty strings
        reasoning = getattr(chunk.choices[0].delta, "reasoning", None) or None
        content = getattr(chunk.choices[0].delta, "content", None) or None

        if reasoning is not None:
            if not printed_reasoning:
                printed_reasoning = True
                print("reasoning:", end="", flush=True)
            print(reasoning, end="", flush=True)
        elif content is not None:
            if not printed_content:
                printed_content = True
                print("\ncontent:", end="", flush=True)
            # Extract and print the content
            print(content, end="", flush=True)
async def on_message(message: cl.Message):
    user_session = cl.user_session.get("session")

    # Extract URLs from the user's message
    urls = extract_urls(message.content)

    futures = []
    with ThreadPoolExecutor() as executor:
        for url in urls:
            futures.append(executor.submit(crawl_url, url))

    results = [future.result() for future in futures]

    for url, result in zip(urls, results):
        ref_number = f"REF_{len(user_session['context']) + 1}"
        user_session["context"][ref_number] = {"url": url, "content": result}

    user_session["history"].append({"role": "user", "content": message.content})

    # Create a system message that includes the context
    context_messages = [
        f'<appendix ref="{ref}">\n{data["content"]}\n</appendix>'
        for ref, data in user_session["context"].items()
    ]
    if context_messages:
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful bot. Use the following context for answering questions. "
                "Refer to the sources using the REF number in square brackets, e.g., [1], only if the source is given in the appendices below.\n\n"
                "If the question requires any information from the provided appendices or context, refer to the sources. "
                "If not, there is no need to add a references section. "
                "At the end of your response, provide a reference section listing the URLs and their REF numbers only if sources from the appendices were used.\n\n"
                "\n\n".join(context_messages)
            ),
        }
    else:
        system_message = {"role": "system", "content": "You are a helpful assistant."}

    msg = cl.Message(content="")
    await msg.send()

    # Get response from the LLM
    stream = await client.chat.completions.create(
        messages=[system_message, *user_session["history"]], stream=True, **settings
    )

    assistant_response = ""
    async for part in stream:
        if token := part.choices[0].delta.content:
            assistant_response += token
            await msg.stream_token(token)

    # Add assistant message to the history
    user_session["history"].append({"role": "assistant", "content": assistant_response})
    await msg.update()

    # Append the reference section to the assistant's response
    reference_section = "\n\nReferences:\n"
    for ref, data in user_session["context"].items():
        reference_section += f"[{ref.split('_')[1]}]: {data['url']}\n"

    msg.content += reference_section
    await msg.update()
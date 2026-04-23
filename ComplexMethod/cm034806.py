async def do_search(
    prompt: str,
    query: Optional[str] = None,
    instructions: str = DEFAULT_INSTRUCTIONS,
    **kwargs
) -> tuple[str, Optional[Sources]]:
    if not prompt or not isinstance(prompt, str):
        return

    if instructions and instructions in prompt:
        return

    if prompt.startswith("##") and query is None:
        return

    if query is None:
        query = prompt.strip().splitlines()[0]

    search_results = await anext(CachedSearch.create_async_generator(
        "",
        [],
        prompt=query,
        **kwargs
    ))

    if instructions:
        new_prompt = f"{search_results}\n\nInstruction: {instructions}\n\nUser request:\n{prompt}"
    else:
        new_prompt = f"{search_results}\n\n{prompt}"

    debug.log(f"Web search: '{query.strip()[:50]}...'")
    debug.log(f"with {len(search_results.results)} Results {search_results.used_words} Words")

    return new_prompt.strip(), search_results.get_sources()
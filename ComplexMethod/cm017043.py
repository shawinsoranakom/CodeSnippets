def translate_page(
    *,
    language: Annotated[str, typer.Option(envvar="LANGUAGE")],
    en_path: Annotated[Path, typer.Option(envvar="EN_PATH")],
) -> None:
    assert language != "en", (
        "`en` is the source language, choose another language as translation target"
    )
    langs = get_langs()
    language_name = langs[language]
    lang_path = Path(f"docs/{language}")
    lang_path.mkdir(exist_ok=True)
    lang_prompt_path = lang_path / "llm-prompt.md"
    assert lang_prompt_path.exists(), f"Prompt file not found: {lang_prompt_path}"
    lang_prompt_content = lang_prompt_path.read_text(encoding="utf-8")

    en_docs_path = Path("docs/en/docs")
    assert str(en_path).startswith(str(en_docs_path)), (
        f"Path must be inside {en_docs_path}"
    )
    out_path = generate_lang_path(lang=language, path=en_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    original_content = en_path.read_text(encoding="utf-8")
    old_translation: str | None = None
    if out_path.exists():
        print(f"Found existing translation: {out_path}")
        old_translation = out_path.read_text(encoding="utf-8")
    print(f"Translating {en_path} to {language} ({language_name})")
    agent = Agent("openai:gpt-5")

    prompt_segments = [
        general_prompt,
        lang_prompt_content,
    ]
    if old_translation:
        prompt_segments.extend(
            [
                "There is an existing previous translation for the original English content, that may be outdated.",
                "Update the translation only where necessary:",
                "- If the original English content has added parts, also add these parts to the translation.",
                "- If the original English content has removed parts, also remove them from the translation, unless you were instructed earlier to not do that in specific cases.",
                "- If parts of the original English content have changed, also change those parts in the translation.",
                "- If the previous translation violates current instructions, update it.",
                "- Otherwise, preserve the original translation LINE-BY-LINE, AS-IS.",
                "Do not:",
                "- rephrase or rewrite correct lines just to improve the style.",
                "- add or remove line breaks, unless the original English content changed.",
                "- change formatting or whitespace unless absolutely required.",
                "Only change what must be changed. The goal is to minimize diffs for easier human review.",
                "UNLESS you were instructed earlier to behave different, there MUST NOT be whole sentences or partial sentences in the updated translation, which are not in the original English content, and there MUST NOT be whole sentences or partial sentences in the original English content, which are not in the updated translation. Remember: the updated translation shall be IN SYNC with the original English content.",
                "Previous translation:",
                f"%%%\n{old_translation}%%%",
            ]
        )
    prompt_segments.extend(
        [
            f"Translate to {language} ({language_name}).",
            "Original content:",
            f"%%%\n{original_content}%%%",
        ]
    )
    prompt = "\n\n".join(prompt_segments)

    MAX_ATTEMPTS = 3
    for attempt_no in range(1, MAX_ATTEMPTS + 1):
        print(f"Running agent for {out_path} (attempt {attempt_no}/{MAX_ATTEMPTS})")
        result = agent.run_sync(prompt)
        out_content = f"{result.output.strip()}\n"
        try:
            check_translation(
                doc_lines=out_content.splitlines(),
                en_doc_lines=original_content.splitlines(),
                lang_code=language,
                auto_fix=False,
                path=str(out_path),
            )
            break  # Exit loop if no errors
        except ValueError as e:
            print(
                f"Translation check failed on attempt {attempt_no}/{MAX_ATTEMPTS}: {e}"
            )
            continue  # Retry if not reached max attempts
    else:  # Max retry attempts reached
        print(f"Translation failed for {out_path} after {MAX_ATTEMPTS} attempts")

    print(f"Saving translation to {out_path}")
    out_path.write_text(out_content, encoding="utf-8", newline="\n")
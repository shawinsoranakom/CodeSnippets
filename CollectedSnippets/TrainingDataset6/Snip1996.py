def llm_translatable_json(
    language: Annotated[str | None, typer.Option(envvar="LANGUAGE")] = None,
) -> None:
    translatable_langs = get_llm_translatable()
    if language:
        if language in translatable_langs:
            print(json.dumps([language]))
            return
        else:
            raise typer.Exit(code=1)
    print(json.dumps(translatable_langs))
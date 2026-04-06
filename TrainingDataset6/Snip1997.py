def commands_json(
    command: Annotated[str | None, typer.Option(envvar="COMMAND")] = None,
) -> None:
    available_commands = [
        "translate-page",
        "translate-lang",
        "update-outdated",
        "add-missing",
        "update-and-add",
        "remove-removable",
    ]
    default_commands = [
        "remove-removable",
        "update-outdated",
        "add-missing",
    ]
    if command:
        if command in available_commands:
            print(json.dumps([command]))
            return
        else:
            raise typer.Exit(code=1)
    print(json.dumps(default_commands))
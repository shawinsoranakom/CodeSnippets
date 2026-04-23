def handle_job_cmds(jobs_cmds: list[str] | None) -> list[str] | None:
    """Handle job commands."""
    export_path = ""
    if jobs_cmds and "export" in jobs_cmds[0]:
        commands = jobs_cmds[0].split("/")
        first_split = commands[0].split(" ")
        if len(first_split) > 1:
            export_path = first_split[1]
        jobs_cmds = ["/".join(commands[1:])]
    if not export_path:
        return jobs_cmds
    if export_path[0] == "~":
        export_path = export_path.replace("~", HOME_DIRECTORY.as_posix())
    elif export_path[0] != "/":
        export_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), export_path
        )

    # Check if the directory exists
    if os.path.isdir(export_path):
        session.console.print(
            f"Export data to be saved in the selected folder: '{export_path}'"
        )
    else:
        os.makedirs(export_path)
        session.console.print(
            f"[green]Folder '{export_path}' successfully created.[/green]"
        )
    return jobs_cmds
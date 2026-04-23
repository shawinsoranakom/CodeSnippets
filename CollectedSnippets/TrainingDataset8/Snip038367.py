def _print_new_version_message() -> None:
    if version.should_show_new_version_notice():
        click.secho(NEW_VERSION_TEXT)
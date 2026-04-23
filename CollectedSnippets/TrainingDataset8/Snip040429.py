def main():
    filenames = _get_filenames(E2E_DIR)
    commands = ["python %s" % filename for filename in filenames]
    failed = run_commands("bare scripts", commands)

    if len(failed) == 0:
        click.secho("All scripts succeeded!", fg="green", bold=True)
        sys.exit(0)
    else:
        click.secho(
            "\n".join(_command_to_string(command) for command in failed), fg="red"
        )
        click.secho("\n%s failed scripts" % len(failed), fg="red", bold=True)
        sys.exit(-1)
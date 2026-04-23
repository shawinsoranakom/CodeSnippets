def main(
    llamafile: Optional[Path] = None,
    llamafile_url: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    force_gpu: bool = False,
):
    print(f"type(llamafile) = {type(llamafile)}")
    if not llamafile:
        if not llamafile_url:
            llamafile = LLAMAFILE
        else:
            llamafile = Path(llamafile_url.rsplit("/", 1)[1])
            if llamafile.suffix != ".llamafile":
                click.echo(
                    click.style(
                        "The given URL does not end with '.llamafile' -> "
                        "can't get filename from URL. "
                        "Specify the filename using --llamafile.",
                        fg="red",
                    ),
                    err=True,
                )
                return

    if llamafile == LLAMAFILE and not llamafile_url:
        llamafile_url = LLAMAFILE_URL
    elif llamafile_url != LLAMAFILE_URL:
        if not click.prompt(
            click.style(
                "You seem to have specified a different URL for the default model "
                f"({llamafile.name}). Are you sure this is correct? "
                "If you want to use a different model, also specify --llamafile.",
                fg="yellow",
            ),
            type=bool,
        ):
            return

    # Go to classic/original_autogpt/scripts/llamafile/
    os.chdir(Path(__file__).resolve().parent)

    on_windows = platform.system() == "Windows"

    if not llamafile.is_file():
        if not llamafile_url:
            click.echo(
                click.style(
                    "Please use --lamafile_url to specify a download URL for "
                    f"'{llamafile.name}'. "
                    "This will only be necessary once, so we can download the model.",
                    fg="red",
                ),
                err=True,
            )
            return

        download_file(llamafile_url, llamafile)

        if not on_windows:
            llamafile.chmod(0o755)
            subprocess.run([llamafile, "--version"], check=True)

    if not on_windows:
        base_command = [f"./{llamafile}"]
    else:
        # Windows does not allow executables over 4GB, so we have to download a
        # model-less llamafile.exe and run that instead.
        if not LLAMAFILE_EXE.is_file():
            download_file(LLAMAFILE_EXE_URL, LLAMAFILE_EXE)
            LLAMAFILE_EXE.chmod(0o755)
            subprocess.run([f".\\{LLAMAFILE_EXE}", "--version"], check=True)

        base_command = [f".\\{LLAMAFILE_EXE}", "-m", llamafile]

    if host:
        base_command.extend(["--host", host])
    if port:
        base_command.extend(["--port", str(port)])
    if force_gpu:
        base_command.extend(["-ngl", "9999"])

    subprocess.run(
        [
            *base_command,
            "--server",
            "--nobrowser",
            "--ctx-size",
            "0",
            "--n-predict",
            "1024",
        ],
        check=True,
    )
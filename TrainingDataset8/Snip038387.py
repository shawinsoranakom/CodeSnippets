def main_run(target, args=None, **kwargs):
    """Run a Python script, piping stderr to Streamlit.

    The script can be local or it can be an url. In the latter case, Streamlit
    will download the script to a temporary file and runs this file.

    """
    from validators import url

    bootstrap.load_config_options(flag_options=kwargs)

    _, extension = os.path.splitext(target)
    if extension[1:] not in ACCEPTED_FILE_EXTENSIONS:
        if extension[1:] == "":
            raise click.BadArgumentUsage(
                "Streamlit requires raw Python (.py) files, but the provided file has no extension.\nFor more information, please see https://docs.streamlit.io"
            )
        else:
            raise click.BadArgumentUsage(
                "Streamlit requires raw Python (.py) files, not %s.\nFor more information, please see https://docs.streamlit.io"
                % extension
            )

    if url(target):
        from streamlit.temporary_directory import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            from urllib.parse import urlparse

            from streamlit import url_util

            path = urlparse(target).path
            main_script_path = os.path.join(
                temp_dir, path.strip("/").rsplit("/", 1)[-1]
            )
            # if this is a GitHub/Gist blob url, convert to a raw URL first.
            target = url_util.process_gitblob_url(target)
            _download_remote(main_script_path, target)
            _main_run(main_script_path, args, flag_options=kwargs)
    else:
        if not os.path.exists(target):
            raise click.BadParameter("File does not exist: {}".format(target))
        _main_run(target, args, flag_options=kwargs)
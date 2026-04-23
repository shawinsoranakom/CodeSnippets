def _download_remote(main_script_path, url_path):
    import requests

    with open(main_script_path, "wb") as fp:
        try:
            resp = requests.get(url_path)
            resp.raise_for_status()
            fp.write(resp.content)
        except requests.exceptions.RequestException as e:
            raise click.BadParameter(("Unable to fetch {}.\n{}".format(url_path, e)))
def install_extension_from_url(dirname, url, branch_name=None):
    check_access()

    if isinstance(dirname, str):
        dirname = dirname.strip()
    if isinstance(url, str):
        url = url.strip()

    assert url, 'No URL specified'

    if dirname is None or dirname == "":
        dirname = get_extension_dirname_from_url(url)

    target_dir = os.path.join(extensions.extensions_dir, dirname)
    assert not os.path.exists(target_dir), f'Extension directory already exists: {target_dir}'

    normalized_url = normalize_git_url(url)
    if any(x for x in extensions.extensions if normalize_git_url(x.remote) == normalized_url):
        raise Exception(f'Extension with this URL is already installed: {url}')

    tmpdir = os.path.join(paths.data_path, "tmp", dirname)

    try:
        shutil.rmtree(tmpdir, True)
        if not branch_name:
            # if no branch is specified, use the default branch
            with git.Repo.clone_from(url, tmpdir, filter=['blob:none']) as repo:
                repo.remote().fetch()
                for submodule in repo.submodules:
                    submodule.update()
        else:
            with git.Repo.clone_from(url, tmpdir, filter=['blob:none'], branch=branch_name) as repo:
                repo.remote().fetch()
                for submodule in repo.submodules:
                    submodule.update()
        try:
            os.rename(tmpdir, target_dir)
        except OSError as err:
            if err.errno == errno.EXDEV:
                # Cross device link, typical in docker or when tmp/ and extensions/ are on different file systems
                # Since we can't use a rename, do the slower but more versatile shutil.move()
                shutil.move(tmpdir, target_dir)
            else:
                # Something else, not enough free space, permissions, etc.  rethrow it so that it gets handled.
                raise err

        import launch
        launch.run_extension_installer(target_dir)

        extensions.list_extensions()
        return [extension_table(), html.escape(f"Installed into {target_dir}. Use Installed tab to restart.")]
    finally:
        shutil.rmtree(tmpdir, True)
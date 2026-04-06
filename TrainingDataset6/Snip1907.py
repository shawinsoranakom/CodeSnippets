def side_effect(old_cmd, command):
    with zipfile.ZipFile(_zip_file(old_cmd), 'r') as archive:
        for file in archive.namelist():
            if not os.path.abspath(file).startswith(os.getcwd()):
                # it's unsafe to overwrite files outside of the current directory
                continue

            try:
                os.remove(file)
            except OSError:
                # does not try to remove directories as we cannot know if they
                # already existed before
                pass
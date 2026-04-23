def hashed_file_path(test, path):
    fullpath = test.render_template(test.static_template_snippet(path))
    return fullpath.removeprefix(settings.STATIC_URL)
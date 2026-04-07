def directory_index(path, fullpath):
    try:
        t = loader.select_template(
            [
                "static/directory_index.html",
                "static/directory_index",
            ]
        )
    except TemplateDoesNotExist:
        with builtin_template_path("directory_index.html").open(encoding="utf-8") as fh:
            t = Engine(libraries={"i18n": "django.templatetags.i18n"}).from_string(
                fh.read()
            )
        c = Context()
    else:
        c = {}
    files = []
    for f in fullpath.iterdir():
        if not f.name.startswith("."):
            url = str(f.relative_to(fullpath))
            if f.is_dir():
                url += "/"
            files.append(url)
    c.update(
        {
            "directory": path + "/",
            "file_list": files,
        }
    )
    return HttpResponse(t.render(c))
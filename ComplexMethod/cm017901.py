def lang_stats(resources=None, languages=None, verbosity=0):
    """
    Output language statistics of committed translation files for each
    Django catalog.
    If resources is provided, it should be a list of translation resource to
    limit the output (e.g. ['core', 'gis']).
    """
    locale_dirs = _get_locale_dirs(resources)

    for name, dir_ in locale_dirs:
        print("\nShowing translations stats for '%s':" % name)
        langs = sorted(d for d in os.listdir(dir_) if not d.startswith("_"))
        for lang in langs:
            if languages and lang not in languages:
                continue
            # TODO: merge first with the latest en catalog
            po_path = "{path}/{lang}/LC_MESSAGES/django{ext}.po".format(
                path=dir_, lang=lang, ext="js" if name.endswith("-js") else ""
            )
            p = run(
                ["msgfmt", "-vc", "-o", "/dev/null", po_path],
                capture_output=True,
                env={"LANG": "C"},
                encoding="utf-8",
                verbosity=verbosity,
            )
            if p.returncode == 0:
                # msgfmt output stats on stderr
                print("%s: %s" % (lang, p.stderr.strip()))
            else:
                print(
                    "Errors happened when checking %s translation for %s:\n%s"
                    % (lang, name, p.stderr)
                )
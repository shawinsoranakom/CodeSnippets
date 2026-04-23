def fetch(resources=None, languages=None, date_since=None, verbosity=0):
    """
    Fetch translations from Transifex, wrap long lines, generate mo files.
    """
    if date_since is None:
        resource_lang_mapping = {}
    else:
        # Filter resources and languages that were updates after `date_since`
        resource_lang_mapping = list_resources_with_updates(
            date_since=date_since,
            resources=resources,
            languages=languages,
            verbosity=verbosity,
        )
        resources = resource_lang_mapping.keys()

    locale_dirs = _get_locale_dirs(resources)
    errors = []

    for name, dir_ in locale_dirs:
        cmd = [
            "tx",
            "pull",
            "-r",
            _tx_resource_for_name(name),
            "-f",
            "--minimum-perc=5",
        ]
        per_resource_langs = resource_lang_mapping.get(name, languages)
        # Transifex pull
        if per_resource_langs is None:
            run([*cmd, "--all"], verbosity=verbosity)
            target_langs = sorted(
                d for d in os.listdir(dir_) if not d.startswith("_") and d != "en"
            )
        else:
            run([*cmd, "-l", ",".join(per_resource_langs)], verbosity=verbosity)
            target_langs = per_resource_langs

        target_langs = [LANG_OVERRIDES.get(d, d) for d in target_langs]

        # msgcat to wrap lines and msgfmt for compilation of .mo file
        for lang in target_langs:
            po_path = "%(path)s/%(lang)s/LC_MESSAGES/django%(ext)s.po" % {
                "path": dir_,
                "lang": lang,
                "ext": "js" if name.endswith("-js") else "",
            }
            if not os.path.exists(po_path):
                print(
                    "No %(lang)s translation for resource %(name)s"
                    % {"lang": lang, "name": name}
                )
                continue
            run(
                ["msgcat", "--no-location", "-o", po_path, po_path], verbosity=verbosity
            )
            msgfmt = run(
                ["msgfmt", "-c", "-o", "%s.mo" % po_path[:-3], po_path],
                verbosity=verbosity,
            )
            if msgfmt.returncode != 0:
                errors.append((name, lang))
    if errors:
        print("\nWARNING: Errors have occurred in following cases:")
        for resource, lang in errors:
            print("\tResource %s for language %s" % (resource, lang))
        exit(1)

    if verbosity:
        print("\nCOMPLETED.")
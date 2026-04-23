def update_catalogs(resources=None, languages=None, verbosity=0):
    """
    Update the en/LC_MESSAGES/django.po (main and contrib) files with
    new/updated translatable strings.
    """
    settings.configure()
    django.setup()
    if resources is not None:
        print("`update_catalogs` will always process all resources.")
    contrib_dirs = _get_locale_dirs(None, include_core=False)

    os.chdir(os.path.join(os.getcwd(), "django"))
    print("Updating en catalogs for Django and contrib apps...")
    call_command("makemessages", locale=["en"], verbosity=verbosity)
    print("Updating en JS catalogs for Django and contrib apps...")
    call_command("makemessages", locale=["en"], domain="djangojs", verbosity=verbosity)

    # Output changed stats
    _check_diff("core", os.path.join(os.getcwd(), "conf", "locale"))
    for name, dir_ in contrib_dirs:
        _check_diff(name, dir_)
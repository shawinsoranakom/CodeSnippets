def update_translation_catalogs():
    """Run makemessages and compilemessages in sampleproject."""
    from django.core.management import call_command

    prev_cwd = os.getcwd()

    os.chdir(proj_dir)
    call_command("makemessages")
    call_command("compilemessages")

    # keep the diff friendly - remove 'POT-Creation-Date'
    pofile = os.path.join(proj_dir, "locale", "fr", "LC_MESSAGES", "django.po")

    with open(pofile) as f:
        content = f.read()
    content = re.sub(r'^"POT-Creation-Date.+$\s', "", content, flags=re.MULTILINE)
    with open(pofile, "w") as f:
        f.write(content)

    os.chdir(prev_cwd)
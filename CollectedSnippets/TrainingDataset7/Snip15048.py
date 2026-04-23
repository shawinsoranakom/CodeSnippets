def _check_diff(cat_name, base_path):
    """
    Output the approximate number of changed/added strings in the en catalog.
    """
    po_path = "%(path)s/en/LC_MESSAGES/django%(ext)s.po" % {
        "path": base_path,
        "ext": "js" if cat_name.endswith("-js") else "",
    }
    p = run(
        "git diff -U0 %s | egrep '^[-+]msgid' | wc -l" % po_path,
        capture_output=True,
        shell=True,
    )
    num_changes = int(p.stdout.strip())
    print("%d changed/added messages in '%s' catalog." % (num_changes, cat_name))
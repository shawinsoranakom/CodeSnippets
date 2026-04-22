def get_version():
    """Get version by parsing out setup.py."""
    dirname = os.path.dirname(__file__)
    base_dir = os.path.abspath(os.path.join(dirname, "../.."))
    pattern = re.compile(r"(?:.*VERSION = \")(?P<version>.*)(?:\"  # PEP-440$)")
    for line in open(os.path.join(base_dir, "setup.py")).readlines():
        m = pattern.match(line)
        if m:
            return m.group("version")
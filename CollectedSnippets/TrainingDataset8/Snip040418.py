def get_current_version():
    """Retrieve the current version by searching for a matching regex ('VERSION=') in setup.py"""
    filename = os.path.join(BASE_DIR, "lib/setup.py")
    regex = r"(?P<pre>.*VERSION = \")(.*)(?P<post>\"  # PEP-440$)"
    pattern = re.compile(regex)

    for line in fileinput.input(filename):
        match = pattern.match(line.rstrip())
        if match:
            return match.groups()[1]

    raise Exception('Did not find regex "%s" for version in setup.py' % (regex))
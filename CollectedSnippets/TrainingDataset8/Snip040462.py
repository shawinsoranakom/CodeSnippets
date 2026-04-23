def update_files(data, version):
    """Update files with new version number."""

    for filename, regex in data.items():
        filename = os.path.join(BASE_DIR, filename)
        matched = False
        pattern = re.compile(regex)
        for line in fileinput.input(filename, inplace=True):
            if pattern.match(line.rstrip()):
                matched = True
            line = re.sub(regex, r"\g<pre>%s\g<post>" % version, line.rstrip())
            print(line)
        if not matched:
            raise Exception('In file "%s", did not find regex "%s"' % (filename, regex))
def update_files(project_name: str, files: Dict[str, str]) -> None:
    """Update files with new project name."""
    for filename, regex in files.items():
        filename = os.path.join(BASE_DIR, filename)
        matched = False
        pattern = re.compile(regex)
        for line in fileinput.input(filename, inplace=True):
            line = line.rstrip()
            if pattern.match(line):
                line = re.sub(
                    regex, rf"\g<pre_match>{project_name}\g<post_match>", line
                )
                matched = True
            print(line)
        if not matched:
            raise Exception(f'In file "{filename}", did not find regex "{regex}"')
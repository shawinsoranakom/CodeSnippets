def _get_cask_install_lines(output):
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('brew cask install'):
            yield line
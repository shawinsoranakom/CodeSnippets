def _get_script_for_brew_cask(output):
    cask_install_lines = _get_cask_install_lines(output)
    if len(cask_install_lines) > 1:
        return shell.and_(*cask_install_lines)
    else:
        return cask_install_lines[0]
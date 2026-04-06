def output():
    return ("Error: Could not symlink bin/gcp\n"
            "Target /usr/local/bin/gcp\n"
            "already exists. You may want to remove it:\n"
            "  rm '/usr/local/bin/gcp'\n"
            "\n"
            "To force the link and overwrite all conflicting files:\n"
            "  brew link --overwrite coreutils\n"
            "\n"
            "To list all files that would be deleted:\n"
            "  brew link --overwrite --dry-run coreutils\n")
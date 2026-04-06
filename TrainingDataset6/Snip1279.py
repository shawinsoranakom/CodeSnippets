def output(target):
    return ('error: the following file has local modifications:\n    {}\n(use '
            '--cached to keep the file, or -f to force removal)').format(target)
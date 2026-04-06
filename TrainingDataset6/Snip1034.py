def new_command(formula):
    return 'brew link --overwrite --dry-run {}'.format(formula)
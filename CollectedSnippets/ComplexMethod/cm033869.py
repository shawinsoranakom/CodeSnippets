def get_shell_plugin(shell_type=None, executable=None):

    if not shell_type:
        # default to sh
        shell_type = 'sh'

        # mostly for backwards compat
        if executable:
            if isinstance(executable, str):
                shell_filename = os.path.basename(executable)
                try:
                    shell = shell_loader.get(shell_filename)
                except Exception:
                    shell = None

                if shell is None:
                    for shell in shell_loader.all():
                        if shell_filename in shell.COMPATIBLE_SHELLS:
                            shell_type = shell.SHELL_FAMILY
                            break
        else:
            raise AnsibleError("Either a shell type or a shell executable must be provided ")

    shell = shell_loader.get(shell_type)
    if not shell:
        raise AnsibleError("Could not find the shell plugin required (%s)." % shell_type)

    if executable:
        setattr(shell, 'executable', executable)

    return shell
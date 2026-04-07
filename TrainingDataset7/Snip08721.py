def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        self.stdout = OutputWrapper(stdout or sys.stdout)
        self.stderr = OutputWrapper(stderr or sys.stderr)
        if no_color and force_color:
            raise CommandError("'no_color' and 'force_color' can't be used together.")
        if no_color:
            self.style = no_style()
        else:
            self.style = color_style(force_color)
            self.stderr.style_func = self.style.ERROR
        if (
            not isinstance(self.requires_system_checks, (list, tuple))
            and self.requires_system_checks != ALL_CHECKS
        ):
            raise TypeError("requires_system_checks must be a list or tuple.")
def update_on_args(self, name, args, kwargs):
        if name == "load":
            # args[2] is index
            self._set_dependent_itervars(args[2])
        else:
            # propagate relevant itervars and is_vec from args
            self.dependent_itervars.update(
                *[
                    arg.dependent_itervars
                    for arg in args
                    if isinstance(arg, CppCSEVariable)
                ]
            )
            if name == "index_expr":
                self._set_dependent_itervars(args[0])
            if any(arg.is_vec for arg in args if isinstance(arg, CppCSEVariable)):
                self.is_vec = True
def set_named_arg(self, args, script_name, arg_elem_id, value, fuzzy=False):
        """Locate an arg of a specific script in script_args and set its value
        Args:
            args: all script args of process p, p.script_args
            script_name: the name target script name to
            arg_elem_id: the elem_id of the target arg
            value: the value to set
            fuzzy: if True, arg_elem_id can be a substring of the control.elem_id else exact match
        Returns:
            Updated script args
        when script_name in not found or arg_elem_id is not found in script controls, raise RuntimeError
        """
        script = next((x for x in self.scripts if x.name == script_name), None)
        if script is None:
            raise RuntimeError(f"script {script_name} not found")

        for i, control in enumerate(script.controls):
            if arg_elem_id in control.elem_id if fuzzy else arg_elem_id == control.elem_id:
                index = script.args_from + i

                if isinstance(args, tuple):
                    return args[:index] + (value,) + args[index + 1:]
                elif isinstance(args, list):
                    args[index] = value
                    return args
                else:
                    raise RuntimeError(f"args is not a list or tuple, but {type(args)}")
        raise RuntimeError(f"arg_elem_id {arg_elem_id} not found in script {script_name}")
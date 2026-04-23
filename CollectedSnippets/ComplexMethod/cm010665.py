def _get_interpreter_name_for_var(var):
        frame = inspect.currentframe()
        if not frame:
            raise RuntimeError("failed to inspect frame")

        i = 0
        while i < frames_up + 1:
            frame = frame.f_back
            if not frame:
                raise RuntimeError("failed to get frame")
            i += 1

        f_locals = frame.f_locals

        for k, v in f_locals.items():
            if isinstance(v, torch.Tensor) and var is v:
                return k if k != "self" else ""
        return ""
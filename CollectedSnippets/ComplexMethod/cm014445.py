def __call__(self, *args, **kwargs):
        # TODO: Check if args or kwargs have more than one different context
        if self._is_context_empty():
            # TODO: Allow CaptureA to take context from mock
            for arg in args:
                if isinstance(arg, Capture) and not arg._is_context_empty():
                    self.ctx = arg.ctx
                    break
            if self._is_context_empty():
                for k, v in kwargs.items():
                    if isinstance(k, Capture) and not k._is_context_empty():
                        self.ctx = k.ctx
                        break
                    if isinstance(v, Capture) and not v._is_context_empty():
                        self.ctx = v.ctx
                        break

        res = CaptureCall(self, ctx=self.ctx, args=args, kwargs=kwargs)
        var = CaptureVariable(None, ctx=self.ctx)
        t = CaptureVariableAssign(ctx=self.ctx, variable=var, value=res)
        self.ctx["operations"].append(t)
        return var
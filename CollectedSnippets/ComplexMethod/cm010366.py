def __call__(self, *args, **kwargs):
        if isinstance(self.subgraph, torch.fx.GraphModule):
            if self._boxed_call:
                # Not all callers respect _boxed_call (e.g. reenter_make_fx).
                if len(args) == 1 and isinstance(args[0], list):
                    return self.ctx.functionalize(self.subgraph)(args[0])
                return self.ctx.functionalize(self.subgraph)(list(args))
            else:
                # Running graph with interpreter is needed for propagating the stack_trace
                with fx_traceback.preserve_node_meta():
                    return self.ctx.functionalize(
                        torch.fx.Interpreter(self.subgraph).run
                    )(*args, **kwargs)
        functionalized = self.ctx.functionalize(self.subgraph)
        if self._boxed_call:
            if len(args) == 1 and isinstance(args[0], list):
                return functionalized(args[0])
            return functionalized(list(args))
        return functionalized(*args, **kwargs)
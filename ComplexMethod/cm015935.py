def observe(self, args):
        # most of this function is just an interpreter for the graph
        # it would be possible to put this in some abstraction, but
        # it is pretty nice to just be able to see exactly what is happening here
        # and hack on it.
        # maybe we should just provide an example interpreter that people copy/paste
        # then edit.
        args_iter = iter(args)
        env = {}

        def load_arg(a):
            return map_arg(a, lambda node: env[node.name])

        for node in self.graph.nodes:
            if node.op == "placeholder":
                result = next(args_iter)
            elif node.op == "get_attr":
                result = self.state_dict[node.target]
            elif node.op == "call_function":
                result = node.target(*load_arg(node.args), **load_arg(node.kwargs))
            elif node.op == "call_method":
                self_obj, *args = load_arg(node.args)
                kwargs = load_arg(node.kwargs)
                result = getattr(self_obj, node.target)(*args, **kwargs)
            elif node.op == "call_module":
                result = self.modules[node.target](
                    *load_arg(node.args), **load_arg(node.kwargs)
                )
            elif node.op == "output":
                return load_arg(node.args[0])

            env[node.name] = result
            root_node, obj = self.matches.get(node.name, (None, None))
            if root_node is node:
                obj.observe(node, env)
            if node.name in self.quants:
                self.quants[node.name].observe(node, env)

        raise RuntimeError("Graph had no output node!")
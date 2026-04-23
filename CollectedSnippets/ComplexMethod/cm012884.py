def get_modules(pattern):
            """Given a node pattern, extract the corresponding modules
            e.g. input: (relu_node, (bn_node, conv_node))
                 output: (relu_module, (bn_module, conv_module))
            """
            if isinstance(pattern, (tuple, list)):
                n, *args = pattern
                modules: list[torch.nn.Module] = []
                modules.append(get_modules(n))
                modules.extend(get_modules(a) for a in args)
                return tuple(modules)
            else:
                n = pattern
                if n.op == "call_module":
                    return named_modules[n.target]
                elif n.op == "call_function" and n.target is torch.nn.functional.relu:
                    relu = torch.nn.ReLU()
                    relu.training = root_module.training
                    return relu
                elif n.op == "call_function" or n.op == "call_method":
                    return n.target
                else:
                    return MatchAllNode
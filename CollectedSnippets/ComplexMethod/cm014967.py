def test_normalize_modules_exhaustive(self):
        """
        Exhaustively test `Node.normalized_arguments` on all standard
        torch.nn Module classes
        """
        for test_params in module_tests + get_new_module_tests():
            if "constructor" not in test_params:
                constructor = getattr(torch.nn, test_params["module_name"])
            else:
                constructor = test_params["constructor"]

            if "constructor_args" not in test_params:
                args = ()
            else:
                args = test_params["constructor_args"]

            mod = constructor(*args)
            # Skip modules that are not standard `torch.nn`
            # instances, including functionals. (functionals
            # are tested in test_normalize_args)
            if mod.__class__.__name__ not in dir(torch.nn):
                continue

            if "input_fn" not in test_params:
                inputs = torch.randn(test_params["input_size"])
            else:
                inputs = test_params["input_fn"]()

            if not isinstance(inputs, (tuple, list)):
                inputs = (inputs,)

            params = ", ".join(f"v{i}" for i in range(len(inputs)))

            # Generate a class to wrap this standard `nn.Module` instance
            test_classname = f"Test{mod.__class__.__name__}"
            test_mod_code = f"""
class {test_classname}(torch.nn.Module):
    def __init__(self, mod):
        super().__init__()
        self.mod = mod

    def forward(self, {params}):
        return self.mod({params})
            """

            gbls = {"torch": torch}
            exec(test_mod_code, gbls)

            test_instance = gbls[test_classname](mod)
            traced = symbolic_trace(test_instance)

            # Use `Node.normalized_arguments` to get a new set of arguments
            # to feed to the Module. Then, rewrite the node to only take
            # in those arguments as kwargs
            modules = dict(traced.named_modules())
            for node in traced.graph.nodes:
                if node.op == "call_module":
                    submod_class = modules[node.target].__class__
                    nn_class = getattr(torch.nn, submod_class.__name__)
                    if submod_class == nn_class:
                        normalized_args = node.normalized_arguments(traced)
                        normalized_args2 = normalize_module(
                            traced, node.target, node.args, node.kwargs
                        )
                        if normalized_args != normalized_args2:
                            raise AssertionError("normalized_args mismatch")
                        if not normalized_args:
                            raise AssertionError("expected normalized_args to be truthy")
                        node.args = normalized_args.args
                        node.kwargs = normalized_args.kwargs

            traced.recompile()

            # These Modules have an RNG in their forward, so testing
            # correctness by comparing outputs is not correct. Skip that
            # check for these
            stochastic_modules = {"FractionalMaxPool2d", "FractionalMaxPool3d", "RReLU"}

            if mod.__class__.__name__ not in stochastic_modules:
                self.assertEqual(traced(*inputs), mod(*inputs))

            traced = NormalizeArgs(symbolic_trace(test_instance)).transform()
            modules = dict(traced.named_modules())
            for node in traced.graph.nodes:
                if node.op == "call_module":
                    submod_class = modules[node.target].__class__
                    nn_class = getattr(torch.nn, submod_class.__name__)
                    if submod_class == nn_class:
                        self.assertEqual(len(node.args), 0)
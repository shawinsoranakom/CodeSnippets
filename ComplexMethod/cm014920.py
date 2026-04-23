def do_test(self):
        if test_name in EXCLUDE_SCRIPT_MODULES:
            return
        if not kwargs.get('check_jit', True):
            raise unittest.SkipTest('module test skipped on JIT')

        default_dtype = torch.get_default_dtype()
        if 'default_dtype' in kwargs and kwargs['default_dtype'] is not None:
            default_dtype = kwargs['default_dtype']

        module_name = get_nn_module_name_from_kwargs(**kwargs)

        if 'constructor' in kwargs:
            nn_module = kwargs['constructor']
        else:
            nn_module = getattr(torch.nn, module_name)

        if "FunctionalModule" in str(nn_module):
            return

        with set_default_dtype(default_dtype):
            if 'constructor_args_fn' in kwargs:
                constructor_args = kwargs['constructor_args_fn']()
            else:
                constructor_args = kwargs.get('constructor_args', ())

            def create_script_module(*args, **kwargs):
                """Construct a script module that passes arguments through to self.submodule"""
                formals, tensors, actuals = get_script_args(args)

                method_args = ', '.join(['self'] + actuals)
                call_args_str = ', '.join(actuals)
                call = f"self.submodule({call_args_str})"
                script = script_method_template.format(method_args, call)

                submodule_constants = []
                if kwargs.get('is_constant'):
                    submodule_constants = ['submodule']

                # Create module to use the script method
                class TheModule(torch.jit.ScriptModule):
                    __constants__ = submodule_constants

                    def __init__(self) -> None:
                        super().__init__()
                        self.submodule = nn_module(*constructor_args)

                def make_module(script):
                    module = TheModule()
                    # check __repr__
                    str(module)
                    module.define(script)
                    return module

                module = make_module(script)
                self.assertExportImportModule(module, tensors)
                create_script_module.last_graph = module.graph
                mod = module(*args)
                return mod

            # Construct a normal nn module to stay consistent with create_script_module
            # and make use of a single global rng_state in module initialization
            def create_nn_module(*args, **kwargs):
                module = nn_module(*constructor_args)
                return module(*args)

            # Set up inputs from tuple of sizes or constructor fn
            dtype = torch.get_default_dtype()
            if 'input_fn' in kwargs:
                input = kwargs['input_fn']()
                if isinstance(input, Tensor):
                    input = (input,)

                if all(tensor.is_complex() for tensor in input):
                    if dtype == torch.float:
                        dtype = torch.cfloat
                    elif dtype == torch.double:
                        dtype = torch.cdouble
                    else:
                        raise AssertionError(f"default_dtype {default_dtype} is not supported")

            else:
                input = (kwargs['input_size'],)

            if 'target_size' in kwargs:
                input = input + (kwargs['target_size'],)
            elif 'target_fn' in kwargs:
                if torch.is_tensor(input):
                    input = (input,)
                input = input + (kwargs['target_fn'](),)
            elif 'target' in kwargs:
                input = input + (kwargs['target'],)

            # Extra parameters to forward()
            if 'extra_args' in kwargs:
                input = input + kwargs['extra_args']

            args_variable, kwargs_variable = create_input(input, dtype=dtype)
            f_args_variable = deepcopy(unpack_variables(args_variable))

            # TODO(issue#52052) Neither this nor no_grad should be required
            # if check_against_reference() is updated to check gradients
            # w.r.t. weights and then only check w.r.t. inputs if any
            # inputs require it.
            any_requires_grad = any(input.requires_grad for input in f_args_variable)

            # Check against Python module as reference
            check_against_reference(self, create_script_module, create_nn_module,
                                    lambda x: x, f_args_variable,
                                    no_grad=no_grad or not any_requires_grad)
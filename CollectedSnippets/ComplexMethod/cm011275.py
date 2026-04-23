def __init__(
        self,
        split_gm: fx.GraphModule,
        num_stages: int,
        has_loss_and_backward: bool,
        loss_spec,
    ):
        # TODO: is there a way not to hard wire init?
        torch.nn.Module.__init__(self)
        self.split_gm: fx.GraphModule = split_gm
        self.executor: DetachExecutor = DetachExecutor(self.split_gm)
        self.num_stages: int = num_stages
        self.has_loss_and_backward = has_loss_and_backward
        self.loss_spec = loss_spec

        for node in split_gm.graph.nodes:
            if not (
                node.op in {"call_module", "placeholder", "output"}
                or (node.op, node.target) == ("call_function", operator.getitem)
                or (node.op, node.target) == ("call_method", "backward")
                or (node.op, node.target) == ("call_function", stage_backward)
                or (node.op, node.target)
                == ("call_function", _null_coalesce_accumulate)
            ):
                raise AssertionError(f"Unexpected node: {node}")

        # Detect replicated parameters so we know that we have to do an additional allreduce
        # before applying the optimizer
        #
        # Note that this also handles the case where there were multiple calls to a single
        # module from different stages, regardless of whether that module invocation
        # was handled by the logic above.

        # Map parameter value to a dictionary that maps the user pipeline module
        # to the local qualname within that module
        params_to_users: dict[torch.nn.Parameter, dict[str, str]] = {}

        for m_qualname, mod in self.split_gm.named_children():
            for p_qualname, param in mod.named_parameters():
                params_to_users.setdefault(param, {})
                params_to_users[param][m_qualname] = p_qualname

        self.replicated_params: list[dict[str, str]] = [
            use_mapping
            for _, use_mapping in params_to_users.items()
            if len(use_mapping) > 1
        ]

        # We must break the aliasing relationship between the replicated parameters for correct
        # numerics in reference runs. If we do not do this, the autograd tape in separate stages
        # will have a reference to the same tensor value and will erroneously apply gradient
        # updates multiple times. Therefore, for each replicated parameter set, we deepcopy the
        # values so that we have separate instances.
        for param_mapping in self.replicated_params:
            for submod_name, param_qualname in param_mapping.items():
                submod = getattr(self.split_gm, submod_name)
                atoms = param_qualname.split(".")
                for atom in atoms[:-1]:
                    submod = getattr(submod, atom)
                setattr(submod, atoms[-1], copy.deepcopy(getattr(submod, atoms[-1])))

        def throw(self, *args, **kwargs):
            raise RuntimeError(
                "To run pipeline locally, invoke the Pipe object directly, not `split_gm`"
            )

        self.split_gm.forward = throw

        # Make submodules use custom direct-serialized GraphModule
        i = 0
        while True:
            try:
                name = get_submod_name(i)
                submod = getattr(self.split_gm, name)
                submod.__class__.__reduce__ = _direct_serialization_reduce
                i += 1
            except AttributeError:
                break
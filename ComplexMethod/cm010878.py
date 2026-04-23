def check_node_safe(node: Node) -> None:
    """
    Checks that the node only uses supported operators. We are starting with very
    conservative cacheability constraints, and incrementally adding more support as we expand.

    [Note: AOTAutograd Cacheability checks]
    - Our cache key is computed from the FX graph produced by Dynamo and the input example values
    - A node is "safe" if the same cache key results in a compiled artifact that has the same behavior
        (i.e, the set of inputs that go into our cache key is sufficient to distinguish its behavior)

    To accomplish this safety check, we consider the following functions to be safe:
        - Public functions under modules torch, torch.functional, and torch.nn.functional: these are
        allowed in the graph by dynamo, so we can assume they are safe to cache.
        - method calls on base tensor types
        - Any call_module that dynamo deemed safe to allow AOTAutograd to trace
        - Non callable nodes, such as placeholder, output, get_attr

    The test suite test_aot_autograd_cache.py::AOTAutogradCachePicklerTests tries its best to fully cover/specify this behavior.
    """
    SAFE_TORCH_MODULES = ("torch.functional", "torch.nn.functional")
    SAFE_TORCH_FUNCTIONS = (
        "torch.Size",
        "torch.Tensor",
        "torch.sym_int",
        "torch._sym_sqrt",
        "torch.sym_float",
        "torch.sym_sum",
        "torch.autograd.grad",
        "torch.distributed.tensor._api.from_local",
    )
    SAFE_NON_TORCH_FUNCTIONS = (
        "einops.einops.rearrange",
        "einops.einops.repeat",
    )

    def is_public_torch_api(target: Callable[..., Any]) -> bool:
        # Don't blindly allow private functions in the torch namespace
        is_private = target.__name__.startswith("_")

        return (
            getattr(target, "__module__", None) in SAFE_TORCH_MODULES and not is_private
        )

    def is_safe_torch_function(target: Callable[..., Any]) -> bool:
        """Allowlisted torch functions"""
        function_name = f"{target.__module__}.{target.__name__}"
        # Allow torch.autograd.function.FunctionCtx if custom autograd functions are allowed
        if function_name == "torch.autograd.function.FunctionCtx":
            return (
                torch._functorch.config.autograd_cache_allow_custom_autograd_functions
            )

        # Functions in torch_non_c_binding_in_graph_functions
        # are guaranteed to be cache safe.
        # See NOTE: [Cacheability of in-graph torch functions]
        return (
            function_name in torch_non_c_binding_in_graph_functions
            or function_name in SAFE_TORCH_FUNCTIONS
            or function_name in torch._inductor.config.unsafe_marked_cacheable_functions
        )

    def is_cacheable_function(target: Callable[..., Any]) -> bool:
        if isinstance(target, (torch._ops.OpOverload, torch._ops.OpOverloadPacket)):
            return True
        if is_public_torch_api(target):
            return True
        # Technically, FXGraphCache._check_for_hop already checks this,
        # but better to error earlier anyway
        if isinstance(target, torch._ops.HigherOrderOperator):
            return target.cacheable()
        is_builtin_fun_or_type = type(target).__name__ == "builtin_function_or_method"
        if is_builtin_fun_or_type:
            return True
        if is_safe_torch_function(target):
            return True
        function_name = f"{target.__module__}.{target.__name__}"
        if function_name in SAFE_NON_TORCH_FUNCTIONS:
            return True
        return False

    def is_tensor(target: Node) -> bool:
        # Tensors always have example values in meta field
        return "example_value" in target.meta

    # I'd love to use a match statement here, but it wasn't introduced until py3.10
    if node.op == "call_function":
        if node.meta and node.meta.get("is_wrapped", False):
            # This is fx.wrap function
            # By default we BypassAOTAutogradCache for unknown functions,
            # But if user explicitly specified cache hash - allow to cache it.
            if node.meta.get("user_cache_hash", None):
                return
        if isinstance(node.target, str):
            raise AssertionError(
                f"expected node.target to not be a string, got {node.target}"
            )
        if not is_cacheable_function(node.target):
            module = getattr(node.target, "__module__", None)
            name = getattr(node.target, "__name__", None)
            raise BypassAOTAutogradCache(
                f"Unsupported call_function target {node.target}. \n Function module: {module}, \nFunction name: {name}"
            )
    elif node.op == "call_method":
        method_name = node.target
        method_target = node.args[0]
        # Only support method calls on base tensors
        if not isinstance(method_target, Node):
            raise AssertionError(
                f"expected method_target to be Node, got {type(method_target)}"
            )
        if not is_tensor(method_target):
            module = getattr(method_target, "__module__", None)
            name = getattr(method_target, "__name__", None)
            raise BypassAOTAutogradCache(
                f"Unsupported call_method target {method_target}. \nMethod module: {module}, \nMethod name: {name}"
            )
        if (
            type(method_name) is not str
            and type(method_name).__name__ != "method_descriptor"
        ):
            raise BypassAOTAutogradCache(
                f"Unsupported call_method method {node.target}: {method_name}"
            )
    # Cache safe
    elif node.op in ("placeholder", "get_attr", "call_module", "output"):
        # Assumption today for call_module being a safe op:
        # (1) today the only call_module ops that can show up in a graph come from "built-in-nn-modules"
        # that dynamo assumes are safe to trace. If dynamo assumes they are safely to blindly trace, then
        # they should be safe to cache as well.
        # (2) in the steady-state (some time in H2?) we shouldn't see these anymore, once inline builtin nn modules by default
        # (3) We do not allow user made nn modules in the graph today, only function calls.
        pass
    else:
        raise BypassAOTAutogradCache(f"Unsupported node op {node.op}")
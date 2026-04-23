def _add_observer_(
    module,
    qconfig_propagation_list=None,
    non_leaf_module_list=None,
    device=None,
    custom_module_class_mapping=None,
):
    r"""Add observer for the leaf child of the module.

    This function insert observer module to all leaf child module that
    has a valid qconfig attribute.

    Args:
        module: input module with qconfig attributes for all the leaf modules that we want to quantize
        qconfig_propagation_list: a list of quantizable modules that will have observers added to them
            if they are leaf nodes
        device: parent device, if any
        non_leaf_module_list: list of non-leaf modules we want to add observer

    Return:
        None, module is modified inplace with added observer modules and forward_hooks
    """
    if qconfig_propagation_list is None:
        qconfig_propagation_list = get_default_qconfig_propagation_list()

    if custom_module_class_mapping is None:
        custom_module_class_mapping = {}

    # respect device affinity when adding observers
    if device is None:
        devices = _get_unique_devices_(module)
        if len(devices) > 1:
            raise AssertionError(
                f"_add_observer_ only works with cpu or single-device CUDA modules, but got devices {devices}"
            )
        device = next(iter(devices)) if len(devices) > 0 else None

    def get_activation_post_process(qconfig, device, special_act_post_process=None):
        activation = (
            qconfig.activation()
            if special_act_post_process is None
            else special_act_post_process()
        )
        if device is not None:
            activation.to(device)
        return activation

    def needs_observation(m):
        return hasattr(m, "qconfig") and m.qconfig is not None

    def insert_activation_post_process(m, special_act_post_process=None):
        """Adds an activation post process module and register
        a pre or post hook that calls the module
        """
        # We don't insert observer/fake_quantize for DeQuantStub
        if needs_observation(m) and not isinstance(m, DeQuantStub):
            # observer and hook will be gone after we swap the module
            m.add_module(
                "activation_post_process",
                get_activation_post_process(
                    m.qconfig, device, special_act_post_process
                ),
            )
            # Register observer as the first entry in the hook list
            # All post forward hooks are preserved and will be executed after the observer before convert
            _register_activation_post_process_hook(
                m, pre_hook=_activation_is_memoryless(m.qconfig)
            )

    for name, child in module.named_children():
        # TODO remove Dropout special after codebase stable
        if type_before_parametrizations(child) is nn.Dropout:
            continue
        elif issubclass(
            type_before_parametrizations(child), (nnq.FloatFunctional, nnq.QFunctional)
        ):
            if needs_observation(child):
                if not hasattr(child, "activation_post_process"):
                    raise AssertionError(
                        f"functional class {type_before_parametrizations(child)} has no pre-defined `activation_post_process`"
                    )
                child.activation_post_process = get_activation_post_process(
                    child.qconfig, device
                )
        elif isinstance(child, _FusedModule):
            # activation_post_process are now added directly to nn.Sequential/_FusedModule
            if needs_observation(child):
                insert_activation_post_process(child)
        elif (
            non_leaf_module_list is not None
            and type_before_parametrizations(child) in non_leaf_module_list
        ):
            if needs_observation(child):
                insert_activation_post_process(child)
        elif _has_special_act_post_process(child):
            special_act_post_process = _get_special_act_post_process(child)
            insert_activation_post_process(child, special_act_post_process)
        elif (
            needs_observation(child)
            and type_before_parametrizations(child) in custom_module_class_mapping
        ):
            observed_class = custom_module_class_mapping[
                type_before_parametrizations(child)
            ]
            observed_child = observed_class.from_float(child)
            setattr(module, name, observed_child)
            # TODO: These are the modules that cannot be observed
            #       Once there are more, we should move them to a separate list
            if not issubclass(observed_class, tuple(no_observer_set())):
                insert_activation_post_process(observed_child)
        else:
            _add_observer_(
                child,
                qconfig_propagation_list,
                non_leaf_module_list,
                device,
                custom_module_class_mapping,
            )

    # Insert observers only for leaf nodes, note that this observer is for
    # the output of the module, for input QuantStub will observe them
    if (
        has_no_children_ignoring_parametrizations(module)
        and not isinstance(module, torch.nn.Sequential)
        and type_before_parametrizations(module) in qconfig_propagation_list
    ):
        insert_activation_post_process(module)
    # This is a special case for AdaRound eager mode
    # AdaRound contains weight_fake_quant to be propagated from API to convert
    # leaf node check with a number of children looks naive assumption that blocks
    # Adding an exception case for AdaRound
    if (
        hasattr(module, "weight_fake_quant")
        and not isinstance(module, torch.nn.Sequential)
        and type_before_parametrizations(module) in qconfig_propagation_list
    ):
        insert_activation_post_process(module)
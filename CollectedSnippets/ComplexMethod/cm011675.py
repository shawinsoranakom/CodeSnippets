def aoti_compile_with_persistent_cache(
    ns: str,
    op_func_name_with_overload: str,
    device_type: str,
    dynamic: bool,
    f: Callable[..., Any],
    args: tuple[Any],
    kwargs: dict[str, Any],
    *,
    dynamic_shapes: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
    remove_runtime_assertions: bool = False,
    disable_constraint_solver: bool = False,
) -> str:
    """
    Compile the given function with persistent cache for AOTI eager mode.
    """
    backend = _aoti_compile_backends.get(device_type)
    if backend:
        return backend.compile_fn(
            ns,
            op_func_name_with_overload,
            device_type,
            dynamic,
            f,
            args,
            kwargs,
            dynamic_shapes=dynamic_shapes,
            options=options,
            remove_runtime_assertions=remove_runtime_assertions,
            disable_constraint_solver=disable_constraint_solver,
        )

    assert not dynamic, "Only support static shape for now"
    flattened_inputs = list(args) + list(kwargs.values())
    if not all(
        isinstance(
            input,
            (
                supported_scalar_types(),
                torch.Tensor,
                list,
                str,
                torch.dtype,
                torch.device,
                torch.layout,
            ),
        )
        for input in flattened_inputs
    ):
        err_msg = f"Unsupported input types: {flattened_inputs}"
        log.exception(err_msg)
        raise NotImplementedError(err_msg)

    for input in flattened_inputs:
        if isinstance(input, list) and not all(
            isinstance(item, torch.Tensor) for item in input
        ):
            err_msg = f"_impl_with_aoti_compile encounters unsupported input types: {flattened_inputs}"
            log.exception(err_msg)
            raise NotImplementedError(err_msg)

    persistent_cache = aoti_eager_cache_dir(ns, device_type)
    if not persistent_cache.exists():
        persistent_cache.mkdir(parents=True)

    persistent_cache_lib = persistent_cache / "lib"
    if not persistent_cache_lib.exists():
        persistent_cache_lib.mkdir()

    with mock.patch.dict(
        os.environ,
        {"TORCHINDUCTOR_CACHE_DIR": persistent_cache_lib.absolute().as_posix()},
    ):
        try:
            kernel_lib_path = torch._export.aot_compile(
                f,
                args,
                kwargs,
                dynamic_shapes=dynamic_shapes,
                remove_runtime_assertions=remove_runtime_assertions,
                disable_constraint_solver=disable_constraint_solver,
                # Some operations may have non-Tensor parameters like int, float, bool. These
                # non-Tensor parameters will not be the input of the graph. Therefore, we do
                # need to keep the same signature.
                same_signature=False,
            )
            assert isinstance(kernel_lib_path, str)

            kernel_metadata_items = []

            for idx, input in enumerate(flattened_inputs):
                if isinstance(input, torch.Tensor):
                    metadata = extract_tensor_metadata(dynamic, input)
                elif isinstance(input, list):
                    assert all(isinstance(item, torch.Tensor) for item in input)
                    metadata = extract_tensor_list_metadata(dynamic, input)
                elif isinstance(input, supported_scalar_types()):
                    metadata = extract_scalar_metadata(device_type, input)
                elif isinstance(input, str):
                    metadata = extract_string_metadata(input)
                elif isinstance(input, torch.dtype):
                    metadata = extract_dtype_metadata(input)
                elif isinstance(input, torch.device):
                    metadata = extract_device_metadata(input)
                elif isinstance(input, torch.layout):
                    metadata = extract_layout_metadata(input)
                else:
                    raise NotImplementedError(f"Unsupported input type: {type(input)}")

                metadata["arg_order"] = idx
                kernel_metadata_items.append(metadata)

            kernel_meta_info: dict[str, Any] = {}
            kernel_meta_info["meta_info"] = kernel_metadata_items
            kernel_meta_info["kernel_path"] = (
                Path(kernel_lib_path).relative_to(persistent_cache).as_posix()
            )

            json_data = []
            update_json = True
            op_conf = persistent_cache / f"{op_func_name_with_overload}.json"
            mode = "r" if op_conf.exists() else "w"
            with aoti_eager_op_conf_lock(op_func_name_with_overload):
                with open(op_conf, mode) as op_conf_file:
                    try:
                        json_data = json.load(op_conf_file)
                    except Exception:
                        json_data = []

                    assert isinstance(json_data, list)
                    for item in json_data:
                        assert isinstance(item, dict)
                        # Same kernel meta info already exists in the json file
                        if item["meta_info"] == kernel_metadata_items:
                            update_json = False
                            break

                if update_json:
                    json_data.append(kernel_meta_info)
                    with open(op_conf, "w") as op_conf_file:
                        json.dump(json_data, op_conf_file, indent=4)

            return kernel_lib_path
        except Exception as e:
            err_msg = f"Failed to compile {op_func_name_with_overload}: {e}"
            log.exception(err_msg)
            return ""
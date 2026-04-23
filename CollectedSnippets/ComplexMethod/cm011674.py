def load_aoti_eager_cache(
    ns: str, op_func_name_with_overload: str, device_type: str
) -> list[dict[str, Any] | None]:
    backend = _aoti_compile_backends.get(device_type)
    if backend:
        return backend.load_fn(ns, op_func_name_with_overload, device_type)

    device_kernel_cache = aoti_eager_cache_dir(ns, device_type)
    op_conf = device_kernel_cache / f"{op_func_name_with_overload}.json"
    if not op_conf.exists():
        return []

    try:
        with aoti_eager_op_conf_lock(op_func_name_with_overload):
            with open(op_conf) as f:
                json_data = json.load(f)
                for item in json_data:
                    # Get absolution path for kernel library
                    kernel_lib_abs_path = device_kernel_cache / item["kernel_path"]
                    item["kernel_path"] = kernel_lib_abs_path.as_posix()

                    # Check if the kernel library exists
                    if not kernel_lib_abs_path.exists():
                        return []

                    for metadata in item["meta_info"]:
                        if metadata.get("is_dynamic"):
                            raise NotImplementedError(
                                "Only support static shape for now"
                            )
                        if (
                            "device_type" in metadata
                            and metadata["device_type"] == "cpu"
                        ):
                            metadata["device_index"] = -1
                        for dtype_key in ["dtype", "dtype_value"]:
                            if dtype_key in metadata:
                                metadata[dtype_key] = getattr(
                                    torch, metadata[dtype_key].split(".")[-1]
                                )
                        if "layout_value" in metadata:
                            metadata["layout_value"] = getattr(
                                torch, metadata["layout_value"].split(".")[-1]
                            )
                        if "memory_format_value" in metadata:
                            metadata["memory_format_value"] = getattr(
                                torch, metadata["memory_format_value"].split(".")[-1]
                            )

                return json_data
    except Exception as e:
        err_msg = f"Failed to load aoti eager cache: {e}"
        log.exception(err_msg)
        return []
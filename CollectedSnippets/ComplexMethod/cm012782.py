def _dump_launch_tensors(args, kernel_path, kernel_hash, kernel_name):
    tensor_list = [arg for arg in args if isinstance(arg, torch.Tensor)]

    run_index = 0

    # Some kernels don't have path and hash stored
    # Using only the name to differentiate between those
    if not kernel_path:
        kernel_hash = kernel_name

    # Saving only the last N runs of the kernels to avoid bloating the folder
    if kernel_hash in inductor_triton_config.debug_dump_kernel_inputs:
        run_index = inductor_triton_config.debug_dump_kernel_inputs[kernel_hash] + 1

        if run_index >= inductor_triton_config.max_kernel_dump_occurrences:
            run_index = 0

    inductor_triton_config.debug_dump_kernel_inputs[kernel_hash] = run_index

    # Default path for kernels with no hash
    if not kernel_path:
        directory_path = os.path.join(cache_dir(), "unhashed_kernel_inputs")
    else:
        directory_path = os.path.dirname(kernel_path)
    directory_path = f"{directory_path}/{kernel_name}_run_{run_index}"
    os.makedirs(directory_path, exist_ok=True)

    log.info(
        "Dumping %d tensor(s) for kernel %s to %s",
        len(tensor_list),
        kernel_name,
        directory_path,
    )

    for index, tensor in enumerate(tensor_list):
        torch.save(tensor, f"{directory_path}/tensor_{index}.pt")
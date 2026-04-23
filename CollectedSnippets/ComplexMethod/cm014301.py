def get_cudnn_version(run_lambda):
    """Return a list of libcudnn.so; it's hard to tell which one is being used."""
    if get_platform() == "win32":
        system_root = os.environ.get("SYSTEMROOT", "C:\\Windows")
        cuda_path = os.environ.get("CUDA_PATH", "%CUDA_PATH%")
        where_cmd = os.path.join(system_root, "System32", "where")
        cudnn_cmd = '{} /R "{}\\bin" cudnn*.dll'.format(where_cmd, cuda_path)
    elif get_platform() == "darwin":
        # CUDA libraries and drivers can be found in /usr/local/cuda/. See
        # https://docs.nvidia.com/cuda/archive/9.0/cuda-installation-guide-mac-os-x/index.html#installation
        # https://docs.nvidia.com/deeplearning/cudnn/installation/latest/
        # Use CUDNN_LIBRARY when cudnn library is installed elsewhere.
        cudnn_cmd = "ls /usr/local/cuda/lib/libcudnn*"
    else:
        cudnn_cmd = 'ldconfig -p | grep libcudnn | rev | cut -d" " -f1 | rev'
    rc, out, _ = run_lambda(cudnn_cmd)
    # find will return 1 if there are permission errors or if not found
    if len(out) == 0 or (rc != 1 and rc != 0):
        l = os.environ.get("CUDNN_LIBRARY")
        if l is not None and os.path.isfile(l):
            return os.path.realpath(l)
        return None
    files_set = set()
    for fn in out.split("\n"):
        fn = os.path.realpath(fn)  # eliminate symbolic links
        if os.path.isfile(fn):
            files_set.add(fn)
    if not files_set:
        return None
    # Alphabetize the result because the order is non-deterministic otherwise
    files = sorted(files_set)
    if len(files) == 1:
        return files[0]
    result = "\n".join(files)
    return "Probably one of the following:\n{}".format(result)
def test_cuda_gds_errors_captured() -> None:
    major_version = int(torch.version.cuda.split(".")[0])
    minor_version = int(torch.version.cuda.split(".")[1])

    if target_os == "windows":
        print(f"{target_os} is not supported for GDS smoke test")
        return

    if major_version < 12 or (major_version == 12 and minor_version < 6):
        print("CUDA version is not supported for GDS smoke test")
        return

    cuda_exception_missed = True
    try:
        print("Testing test_cuda_gds_errors_captured")
        with NamedTemporaryFile() as f:
            torch.cuda.gds.GdsFile(f.name, os.O_CREAT | os.O_RDWR)
        # cuFile >= 1.17 (CUDA 13.2+) compat mode: registration succeeds
        # without nvidia-fs driver, falling back to POSIX I/O
        if major_version > 13 or (major_version == 13 and minor_version >= 2):
            print("GDS handle registered successfully via compatibility mode")
            cuda_exception_missed = False
    except RuntimeError as e:
        expected_error = "cuFileHandleRegister failed"
        if re.search(expected_error, f"{e}"):
            print(f"Caught expected CUDA exception: {e}")
            cuda_exception_missed = False
        else:
            raise e
    if cuda_exception_missed:
        raise RuntimeError(
            "Expected cuFileHandleRegister failed RuntimeError but have not received!"
        )
def _init():
        global __cudnn_version
        if __cudnn_version is None:
            # pyrefly: ignore [missing-attribute]
            __cudnn_version = _cudnn.getVersionInt()
            # pyrefly: ignore [missing-attribute]
            runtime_version = _cudnn.getRuntimeVersion()
            # pyrefly: ignore [missing-attribute]
            compile_version = _cudnn.getCompileVersion()
            runtime_major, runtime_minor, _ = runtime_version
            compile_major, compile_minor, _ = compile_version
            # Different major versions are always incompatible
            # Starting with cuDNN 7, minor versions are backwards-compatible
            # Not sure about MIOpen (ROCm), so always do a strict check
            if runtime_major != compile_major:
                cudnn_compatible = False
            # pyrefly: ignore [missing-attribute]
            elif runtime_major < 7 or not _cudnn.is_cuda:
                cudnn_compatible = runtime_minor == compile_minor
            else:
                cudnn_compatible = runtime_minor >= compile_minor
            if not cudnn_compatible:
                if os.environ.get("PYTORCH_SKIP_CUDNN_COMPATIBILITY_CHECK", "0") == "1":
                    return True
                base_error_msg = (
                    f"cuDNN version incompatibility: "
                    f"PyTorch was compiled  against {compile_version} "
                    f"but found runtime version {runtime_version}. "
                    f"PyTorch already comes bundled with cuDNN. "
                    f"One option to resolving this error is to ensure PyTorch "
                    f"can find the bundled cuDNN. "
                )

                if "LD_LIBRARY_PATH" in os.environ:
                    ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
                    if any(
                        substring in ld_library_path for substring in ["cuda", "cudnn"]
                    ):
                        raise RuntimeError(
                            f"{base_error_msg}"
                            f"Looks like your LD_LIBRARY_PATH contains incompatible version of cudnn. "
                            f"Please either remove it from the path or install cudnn {compile_version}"
                        )
                    else:
                        raise RuntimeError(
                            f"{base_error_msg}"
                            f"one possibility is that there is a "
                            f"conflicting cuDNN in LD_LIBRARY_PATH."
                        )
                else:
                    raise RuntimeError(base_error_msg)
            # Check if cuDNN version is compatible with available CUDA devices
            if torch.cuda.is_available() and not torch.version.hip:
                min_cc = min(
                    [
                        torch.cuda.get_device_capability(i)
                        for i in range(torch.cuda.device_count())
                    ]
                )
                if __cudnn_version >= 91100 and min_cc < (7, 5):
                    raise RuntimeError(
                        f"cuDNN version {__cudnn_version} is not compatible with devices with SM < 7.5. "
                        f"Please install a version of PyTorch with a compatible cuDNN version. "
                        f"https://github.com/pytorch/pytorch/blob/main/RELEASE.md#release-compatibility-matrix"
                    )

        return True
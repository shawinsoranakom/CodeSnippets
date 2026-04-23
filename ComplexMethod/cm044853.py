def load_nvrtc():
    import torch

    if not torch.cuda.is_available():
        print("[INFO] CUDA is not available, skipping nvrtc setup.")
        return

    if sys.platform == "win32":
        torch_lib_dir = Path(torch.__file__).parent / "lib"
        if torch_lib_dir.exists():
            os.add_dll_directory(str(torch_lib_dir))
            print(f"[INFO] Added DLL directory: {torch_lib_dir}")
            matching_files = sorted(torch_lib_dir.glob("nvrtc*.dll"))
            if not matching_files:
                print(f"[ERROR] No nvrtc*.dll found in {torch_lib_dir}")
                return
            for dll_path in matching_files:
                dll_name = os.path.basename(dll_path)
                try:
                    ctypes.CDLL(dll_name)
                    print(f"[INFO] Loaded: {dll_name}")
                except OSError as e:
                    print(f"[WARNING] Failed to load {dll_name}: {e}")
        else:
            print(f"[WARNING] Torch lib directory not found: {torch_lib_dir}")

    elif sys.platform == "linux":
        site_packages = Path(torch.__file__).resolve().parents[1]
        nvrtc_dir = site_packages / "nvidia" / "cuda_nvrtc" / "lib"

        if not nvrtc_dir.exists():
            print(f"[ERROR] nvrtc dir not found: {nvrtc_dir}")
            return

        matching_files = sorted(nvrtc_dir.glob("libnvrtc*.so*"))
        if not matching_files:
            print(f"[ERROR] No libnvrtc*.so* found in {nvrtc_dir}")
            return

        for so_path in matching_files:
            try:
                ctypes.CDLL(so_path, mode=ctypes.RTLD_GLOBAL)  # type: ignore
                print(f"[INFO] Loaded: {so_path}")
            except OSError as e:
                print(f"[WARNING] Failed to load {so_path}: {e}")
def _find_llama_server_binary() -> Optional[str]:
        """
        Locate the llama-server binary.

        Search order:
        1.  LLAMA_SERVER_PATH environment variable (direct path to binary)
        1b. UNSLOTH_LLAMA_CPP_PATH env var (custom llama.cpp install dir)
        2.  ~/.unsloth/llama.cpp/llama-server        (make build, root dir)
        3.  ~/.unsloth/llama.cpp/build/bin/llama-server  (cmake build, Linux)
        4.  ~/.unsloth/llama.cpp/build/bin/Release/llama-server.exe  (cmake build, Windows)
        5.  ./llama.cpp/llama-server                 (legacy: make build, root dir)
        6.  ./llama.cpp/build/bin/llama-server        (legacy: cmake in-tree build)
        7.  llama-server on PATH                     (system install)
        8.  ./bin/llama-server                       (legacy: extracted binary)
        """
        import os
        import sys

        binary_name = "llama-server.exe" if sys.platform == "win32" else "llama-server"

        # 1. Env var — direct path to binary
        env_path = os.environ.get("LLAMA_SERVER_PATH")
        if env_path and Path(env_path).is_file():
            return env_path

        # 1b. UNSLOTH_LLAMA_CPP_PATH — custom llama.cpp install directory
        custom_llama_cpp = os.environ.get("UNSLOTH_LLAMA_CPP_PATH")
        if custom_llama_cpp:
            custom_dir = Path(custom_llama_cpp)
            # Root dir (make builds)
            root_bin = custom_dir / binary_name
            if root_bin.is_file():
                return str(root_bin)
            # build/bin/ (cmake builds on Linux)
            cmake_bin = custom_dir / "build" / "bin" / binary_name
            if cmake_bin.is_file():
                return str(cmake_bin)
            # build/bin/Release/ (cmake builds on Windows)
            if sys.platform == "win32":
                win_bin = custom_dir / "build" / "bin" / "Release" / binary_name
                if win_bin.is_file():
                    return str(win_bin)

        # 2–4. ~/.unsloth/llama.cpp (primary — setup.sh / setup.ps1 build here)
        unsloth_home = Path.home() / ".unsloth" / "llama.cpp"
        # Root dir (make builds copy binaries here)
        home_root = unsloth_home / binary_name
        if home_root.is_file():
            return str(home_root)
        # build/bin/ (cmake builds on Linux)
        home_linux = unsloth_home / "build" / "bin" / binary_name
        if home_linux.is_file():
            return str(home_linux)

        # 3. Windows MSVC build has Release subdir
        if sys.platform == "win32":
            home_win = unsloth_home / "build" / "bin" / "Release" / binary_name
            if home_win.is_file():
                return str(home_win)

        # 5–6. Legacy: in-tree build (older setup.sh / setup.ps1 versions)
        project_root = Path(__file__).resolve().parents[4]
        # Root dir (make builds)
        root_path = project_root / "llama.cpp" / binary_name
        if root_path.is_file():
            return str(root_path)
        # build/bin/ (cmake builds)
        build_path = project_root / "llama.cpp" / "build" / "bin" / binary_name
        if build_path.is_file():
            return str(build_path)
        if sys.platform == "win32":
            win_path = (
                project_root / "llama.cpp" / "build" / "bin" / "Release" / binary_name
            )
            if win_path.is_file():
                return str(win_path)

        # 7. System PATH
        system_path = shutil.which("llama-server")
        if system_path:
            return system_path

        # 8. Legacy: extracted to bin/
        bin_path = project_root / "bin" / binary_name
        if bin_path.is_file():
            return str(bin_path)

        return None
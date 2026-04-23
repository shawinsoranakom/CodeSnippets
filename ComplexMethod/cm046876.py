def install_llama_cpp_old(version = -10):
    # Download the 10th latest release since the latest might be broken!
    # FALLBACK mechanism
    releases = subprocess.check_output(
        ["git", "ls-remote", "--tags", "https://github.com/ggerganov/llama.cpp.git"]
    )
    releases = releases.decode("utf-8").replace("\t", " ").split("\n")
    for i, x in enumerate(releases):
        if "refs/tags/b" not in x:
            break
    releases = releases[:i]
    latest = releases[-1]
    version = releases[version].split(" ")[0]

    # Check if the llama.cpp exists
    if os.path.exists("llama.cpp"):
        print(
            "**[WARNING]** You have a llama.cpp directory which is broken.\n"
            "Unsloth will DELETE the broken directory and install a new one.\n"
            "Press CTRL + C / cancel this if this is wrong. We shall wait 30 seconds.\n"
        )
        import time

        for i in range(30):
            print(f"**[WARNING]** Deleting llama.cpp directory... {30-i} seconds left.")
            time.sleep(1)
        import shutil

        shutil.rmtree("llama.cpp", ignore_errors = True)

    # Clone a specific commit
    # Also don't use the GPU!
    commands = [
        "git clone --recursive https://github.com/ggerganov/llama.cpp",
        f"cd llama.cpp && git reset --hard {version} && git clean -df",
    ]
    try_execute(commands)

    # Try using MAKE
    commands = [
        "make clean -C llama.cpp",
        f"make all -j{(psutil.cpu_count() or 1)*2} -C llama.cpp",
    ]
    if try_execute(commands) == "CMAKE":
        # Instead use CMAKE
        commands = [
            f"cmake llama.cpp -B llama.cpp/build -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=OFF {CURL_FLAG}",
            f"cmake --build llama.cpp/build --config Release -j{(psutil.cpu_count() or 1)*2} --clean-first --target {' '.join(LLAMA_CPP_TARGETS)}",
            "cp llama.cpp/build/bin/llama-* llama.cpp",
            "rm -rf llama.cpp/build",
        ]

        try_execute(commands)

    # Check if successful
    if not (
        os.path.exists("llama.cpp/llama-quantize.exe")
        or os.path.exists("llama.cpp/llama-quantize")
        or os.path.exists("llama.cpp/quantize.exe")
        or os.path.exists("llama.cpp/quantize")
        or os.path.exists("llama.cpp/build/bin/llama-quantize")
        or os.path.exists("llama.cpp/build/bin/quantize")
    ):
        raise RuntimeError(
            "Unsloth: The file 'llama.cpp/llama-quantize' or `llama.cpp/quantize` does not exist.\n"
            "We've also double checked the building directory under 'llama.cpp/build/bin/'.\n"
            "But we expect this file to exist! Check if the file exists under llama.cpp and investigate the building process of llama.cpp (make/cmake)!"
        )
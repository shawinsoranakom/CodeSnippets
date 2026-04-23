def setup_ci():
    if "GITHUB_ACTIONS" in os.environ:
        # Enable emulator hardware acceleration
        # (https://github.blog/changelog/2024-04-02-github-actions-hardware-accelerated-android-virtualization-now-available/).
        if platform.system() == "Linux":
            run(
                ["sudo", "tee", "/etc/udev/rules.d/99-kvm4all.rules"],
                input='KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"\n',
                text=True,
            )
            run(["sudo", "udevadm", "control", "--reload-rules"])
            run(["sudo", "udevadm", "trigger", "--name-match=kvm"])

        # Free up disk space by deleting unused versions of the NDK
        # (https://github.com/freakboy3742/pyspamsum/pull/108).
        for line in ENV_SCRIPT.read_text().splitlines():
            if match := re.fullmatch(r"ndk_version=(.+)", line):
                ndk_version = match[1]
                break
        else:
            raise ValueError(f"Failed to find NDK version in {ENV_SCRIPT.name}")

        for item in (android_home / "ndk").iterdir():
            if item.name[0].isdigit() and item.name != ndk_version:
                delete_glob(item)
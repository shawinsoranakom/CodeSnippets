def get_pkg_version(run_lambda, pkg):
    assert get_platform() == "linux"

    if pkg == "vllm_xpu_kernels":
        rc, out, _ = run_lambda("pip show vllm-xpu-kernels")
        if rc == 0:
            match = re.search(r"Version: (.*)", out)
            return match.group(1).strip() if match else None
        return None

    pkg_map = {
        "igc": ["intel-igc-core", "libigc2", "libigc1"],
        "level_zero_loader": ["level-zero", "libze1"],
        "level_zero_driver": ["libze-intel-gpu1", "intel-level-zero-gpu"],
        "oneccl": ["intel-oneapi-ccl", "oneccl"],
        "libigdgmm": ["libigdgmm12", "libigdgmm"],
    }

    pkg_candidates = pkg_map.get(pkg, [])
    if not pkg_candidates:
        return None

    mgr_name = None
    for mgr in ["dpkg", "dnf", "yum", "zypper"]:
        rc, _, _ = run_lambda(f"which {mgr}")
        if rc == 0:
            mgr_name = mgr
            break

    if not mgr_name:
        return None

    ret = ""
    index = -1

    for pkg_name in pkg_candidates:
        if not pkg_name:
            continue

        cmd = ""
        if mgr_name in ["dnf", "yum"]:
            index = 1
            cmd = f"{mgr_name} list | grep -w {pkg_name}"
        elif mgr_name == "zypper":
            index = 2
            cmd = f"{mgr_name} info {pkg_name} | grep Version"
        elif mgr_name == "dpkg":
            index = 2
            cmd = f"{mgr_name} -l | grep -w {pkg_name}"

        if cmd:
            out = run_and_read_all(run_lambda, cmd)
            if out:
                ret = out.splitlines()[0]
                break

    if not ret or index == -1:
        return None

    lst = re.sub(" +", " ", ret).strip().split(" ")
    if len(lst) > index:
        return lst[index]

    return None
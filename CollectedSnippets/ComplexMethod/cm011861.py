def valid_vec_isa_list() -> list[VecISA]:
    isa_list: list[VecISA] = []
    if sys.platform == "darwin" and platform.processor() == "arm":
        isa_list.append(VecNEON())

    if sys.platform not in ["linux", "win32"]:
        return isa_list

    arch = platform.machine()
    if arch == "s390x":
        with open("/proc/cpuinfo") as _cpu_info:
            while True:
                line = _cpu_info.readline()
                if not line:
                    break
                # process line
                featuresmatch = re.match(r"^features\s*:\s*(.*)$", line)
                if featuresmatch:
                    for group in featuresmatch.groups():
                        if re.search(r"[\^ ]+vxe[\$ ]+", group):
                            isa_list.append(VecZVECTOR())
                            break
    elif arch == "ppc64le":
        isa_list.append(VecVSX())
    elif arch == "aarch64":
        if torch.backends.cpu.get_cpu_capability() == "SVE256":
            isa_list.append(VecSVE256())
        else:
            isa_list.append(VecNEON())

    elif arch in ["x86_64", "AMD64"]:
        """
        arch value is x86_64 on Linux, and the value is AMD64 on Windows.
        """
        _cpu_supported_x86_isa = x86_isa_checker()
        isa_list.extend(
            isa
            for isa in supported_vec_isa_list
            if all(flag in _cpu_supported_x86_isa for flag in str(isa).split()) and isa
        )

    return isa_list
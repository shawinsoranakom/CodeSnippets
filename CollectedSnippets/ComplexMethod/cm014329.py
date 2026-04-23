def _get_cuda_arch_flags(cflags: list[str] | None = None) -> list[str]:
    """
    Determine CUDA arch flags to use.

    For an arch, say "6.1", the added compile flag will be
    ``-gencode=arch=compute_61,code=sm_61``.
    For an added "+PTX", an additional
    ``-gencode=arch=compute_xx,code=compute_xx`` is added.

    See select_compute_arch.cmake for corresponding named and supported arches
    when building with CMake.
    """
    # If cflags is given, there may already be user-provided arch flags in it
    # (from `extra_compile_args`)
    if cflags is not None:
        for flag in cflags:
            if 'TORCH_EXTENSION_NAME' in flag:
                continue
            if 'arch' in flag:
                return []

    # Note: keep combined names ("arch1+arch2") above single names, otherwise
    # string replacement may not do the right thing
    named_arches = collections.OrderedDict([
        ('Kepler+Tesla', '3.7'),
        ('Kepler', '3.5+PTX'),
        ('Maxwell+Tegra', '5.3'),
        ('Maxwell', '5.0;5.2+PTX'),
        ('Pascal', '6.0;6.1+PTX'),
        ('Volta+Tegra', '7.2'),
        ('Volta', '7.0+PTX'),
        ('Turing', '7.5+PTX'),
        ('Ampere+Tegra', '8.7'),
        ('Ampere', '8.0;8.6+PTX'),
        ('Ada', '8.9+PTX'),
        ('Hopper', '9.0+PTX'),
        ('Blackwell+Tegra', '11.0'),
        ('Blackwell', '10.0;10.3;12.0;12.1+PTX'),
    ])

    supported_arches = ['3.5', '3.7', '5.0', '5.2', '5.3', '6.0', '6.1', '6.2',
                        '7.0', '7.2', '7.5', '8.0', '8.6', '8.7', '8.9', '9.0', '9.0a',
                        '10.0', '10.0a', '11.0', '11.0a', '10.3', '10.3a', '12.0',
                        '12.0a', '12.1', '12.1a']
    valid_arch_strings = supported_arches + [s + "+PTX" for s in supported_arches]

    # The default is sm_30 for CUDA 9.x and 10.x
    # First check for an env var (same as used by the main setup.py)
    # Can be one or more architectures, e.g. "6.1" or "3.5;5.2;6.0;6.1;7.0+PTX"
    # See cmake/Modules_CUDA_fix/upstream/FindCUDA/select_compute_arch.cmake
    _arch_list = os.environ.get('TORCH_CUDA_ARCH_LIST', None)

    # If not given or set as native, determine what's best for the GPU / CUDA version that can be found
    if not _arch_list or _arch_list == "native":
        arch_list = []
        # the assumption is that the extension should run on any of the currently visible cards,
        # which could be of different types - therefore all archs for visible cards should be included
        for i in range(torch.cuda.device_count()):
            capability = torch.cuda.get_device_capability(i)
            supported_sm = [int("".join(re.findall(r"\d+", arch.split('_')[1])))
                            for arch in torch.cuda.get_arch_list() if 'sm_' in arch]
            max_supported_sm = max((sm // 10, sm % 10) for sm in supported_sm)
            # Capability of the device may be higher than what's supported by the user's
            # NVCC, causing compilation error. User's NVCC is expected to match the one
            # used to build pytorch, so we use the maximum supported capability of pytorch
            # to clamp the capability.
            capability = min(max_supported_sm, capability)
            arch = f'{capability[0]}.{capability[1]}'
            if arch not in arch_list:
                arch_list.append(arch)
        arch_list = sorted(arch_list)
        arch_list[-1] += '+PTX'

        if not _arch_list:
            # Only log on rank 0 in distributed settings to avoid spam
            if not torch.distributed.is_available() or not torch.distributed.is_initialized() or torch.distributed.get_rank() == 0:
                arch_list_str = ';'.join(arch_list)
                logger.debug(
                    "TORCH_CUDA_ARCH_LIST is not set, using TORCH_CUDA_ARCH_LIST='%s' "
                    "for visible GPU architectures. Set os.environ['TORCH_CUDA_ARCH_LIST'] to override.",
                    arch_list_str)
    else:
        # Deal with lists that are ' ' separated (only deal with ';' after)
        _arch_list = _arch_list.replace(' ', ';')
        # Expand named arches
        for named_arch, archival in named_arches.items():
            _arch_list = _arch_list.replace(named_arch, archival)

        arch_list = _arch_list.split(';')

    flags = []
    for arch in arch_list:
        if arch not in valid_arch_strings:
            raise ValueError(f"Unknown CUDA arch ({arch}) or GPU not supported")
        else:
            # Handle both single and double-digit architecture versions
            version = arch.split('+')[0]  # Remove "+PTX" if present
            major, minor = version.split('.')
            num = f"{major}{minor}"
            flags.append(f'-gencode=arch=compute_{num},code=sm_{num}')
            if arch.endswith('+PTX'):
                flags.append(f'-gencode=arch=compute_{num},code=compute_{num}')

    return sorted(set(flags))
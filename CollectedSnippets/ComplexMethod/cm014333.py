def _write_ninja_file(path,
                      cflags,
                      post_cflags,
                      cuda_cflags,
                      cuda_post_cflags,
                      cuda_dlink_post_cflags,
                      sycl_cflags,
                      sycl_post_cflags,
                      sycl_dlink_post_cflags,
                      sources,
                      objects,
                      ldflags,
                      library_target,
                      with_cuda,
                      with_sycl) -> None:
    r"""Write a ninja file that does the desired compiling and linking.

    `path`: Where to write this file
    `cflags`: list of flags to pass to $cxx. Can be None.
    `post_cflags`: list of flags to append to the $cxx invocation. Can be None.
    `cuda_cflags`: list of flags to pass to $nvcc. Can be None.
    `cuda_post_cflags`: list of flags to append to the $nvcc invocation. Can be None.
    `cuda_dlink_post_cflags`: list of flags to append to the $nvcc device code link invocation. Can be None.
    `sycl_cflags`: list of flags to pass to SYCL compiler. Can be None.
    `sycl_post_cflags`: list of flags to append to the SYCL compiler invocation. Can be None.
    `sycl_dlink_post_cflags`: list of flags to append to the SYCL compiler device code link invocation. Can be None.
e.
    `sources`: list of paths to source files
    `objects`: list of desired paths to objects, one per source.
    `ldflags`: list of flags to pass to linker. Can be None.
    `library_target`: Name of the output library. Can be None; in that case,
                      we do no linking.
    `with_cuda`: If we should be compiling with CUDA.
    """
    def sanitize_flags(flags):
        if flags is None:
            return []
        else:
            return [flag.strip() for flag in flags]

    cflags = sanitize_flags(cflags)
    post_cflags = sanitize_flags(post_cflags)
    cuda_cflags = sanitize_flags(cuda_cflags)
    cuda_post_cflags = sanitize_flags(cuda_post_cflags)
    cuda_dlink_post_cflags = sanitize_flags(cuda_dlink_post_cflags)
    sycl_cflags = sanitize_flags(sycl_cflags)
    sycl_post_cflags = sanitize_flags(sycl_post_cflags)
    sycl_dlink_post_cflags = sanitize_flags(sycl_dlink_post_cflags)
    ldflags = sanitize_flags(ldflags)

    # Sanity checks...
    if len(sources) != len(objects):
        raise AssertionError("sources and objects lists must be the same length")
    if len(sources) == 0:
        raise AssertionError("At least one source is required to build a library")

    compiler = get_cxx_compiler()

    # Version 1.3 is required for the `deps` directive.
    config = ['ninja_required_version = 1.3']
    config.append(f'cxx = {compiler}')
    if with_cuda or cuda_dlink_post_cflags:
        if "PYTORCH_NVCC" in os.environ:
            nvcc = os.getenv("PYTORCH_NVCC")    # user can set nvcc compiler with ccache using the environment variable here
        else:
            if IS_HIP_EXTENSION:
                nvcc = _get_hipcc_path()
            else:
                nvcc = _join_cuda_home('bin', 'nvcc')
        config.append(f'nvcc = {nvcc}')
    if with_sycl or sycl_dlink_post_cflags:
        sycl = 'icx' if IS_WINDOWS else 'icpx'
        config.append(f'sycl = {sycl}')

    if IS_HIP_EXTENSION:
        post_cflags = COMMON_HIP_FLAGS + post_cflags
    flags = [f'cflags = {" ".join(cflags)}']
    flags.append(f'post_cflags = {" ".join(post_cflags)}')
    if with_cuda:
        flags.append(f'cuda_cflags = {" ".join(cuda_cflags)}')
        flags.append(f'cuda_post_cflags = {" ".join(cuda_post_cflags)}')
    flags.append(f'cuda_dlink_post_cflags = {" ".join(cuda_dlink_post_cflags)}')
    if with_sycl:
        flags.append(f'sycl_cflags = {" ".join(sycl_cflags)}')
        flags.append(f'sycl_post_cflags = {" ".join(sycl_post_cflags)}')
    flags.append(f'sycl_dlink_post_cflags = {" ".join(sycl_dlink_post_cflags)}')
    flags.append(f'ldflags = {" ".join(ldflags)}')

    # Turn into absolute paths so we can emit them into the ninja build
    # file wherever it is.
    sources = [os.path.abspath(file) for file in sources]

    # See https://ninja-build.org/build.ninja.html for reference.
    compile_rule = ['rule compile']
    if IS_WINDOWS:
        compiler_name = "$cxx" if IS_HIP_EXTENSION else "cl"
        compile_rule.append(
            f'  command = {compiler_name} '
            '/showIncludes $cflags -c $in /Fo$out $post_cflags'  # codespell:ignore
        )
        if not IS_HIP_EXTENSION:
            compile_rule.append('  deps = msvc')
    else:
        compile_rule.append(
            '  command = $cxx -MMD -MF $out.d $cflags -c $in -o $out $post_cflags')
        compile_rule.append('  depfile = $out.d')
        compile_rule.append('  deps = gcc')

    if with_cuda:
        cuda_compile_rule = ['rule cuda_compile']
        nvcc_gendeps = ''
        # -MD is not supported by ROCm
        # Nvcc flag `-MD` is not supported by sccache, which may increase build time.
        if torch.version.cuda is not None and os.getenv('TORCH_EXTENSION_SKIP_NVCC_GEN_DEPENDENCIES', '0') != '1':
            cuda_compile_rule.append('  depfile = $out.d')
            cuda_compile_rule.append('  deps = gcc')
            # Note: non-system deps with nvcc are only supported
            # on Linux so use -MD to make this work on Windows too.
            nvcc_gendeps = '-MD -MF $out.d'
        cuda_compile_rule.append(
            f'  command = $nvcc {nvcc_gendeps} $cuda_cflags -c $in -o $out $cuda_post_cflags')

    if with_sycl:
        sycl_compile_rule = ['rule sycl_compile']
        # SYCL compiler does not recognize .sycl extension automatically,
        # so we pass '-x c++' explicitly notifying compiler of file format
        sycl_compile_rule.append(
            '  command = $sycl $sycl_cflags -c -x c++ $in -o $out $sycl_post_cflags')


    # Emit one build rule per source to enable incremental build.
    build = []
    for source_file, object_file in zip(sources, objects, strict=True):
        is_cuda_source = _is_cuda_file(source_file) and with_cuda
        is_sycl_source = _is_sycl_file(source_file) and with_sycl
        if is_cuda_source:
            rule = 'cuda_compile'
        elif is_sycl_source:
            rule = 'sycl_compile'
        else:
            rule = 'compile'
        if IS_WINDOWS:
            source_file = source_file.replace(':', '$:')
            object_file = object_file.replace(':', '$:')
        source_file = source_file.replace(" ", "$ ")
        object_file = object_file.replace(" ", "$ ")
        build.append(f'build {object_file}: {rule} {source_file}')

    if cuda_dlink_post_cflags:
        cuda_devlink_out = os.path.join(os.path.dirname(objects[0]), 'dlink.o')
        cuda_devlink_rule = ['rule cuda_devlink']
        cuda_devlink_rule.append('  command = $nvcc $in -o $out $cuda_dlink_post_cflags')
        cuda_devlink = [f'build {cuda_devlink_out}: cuda_devlink {" ".join(objects)}']
        objects += [cuda_devlink_out]
    else:
        cuda_devlink_rule, cuda_devlink = [], []

    if sycl_dlink_post_cflags:
        sycl_devlink_out = os.path.join(os.path.dirname(objects[0]), "sycl_dlink.o")
        if IS_WINDOWS:
            sycl_devlink_objects = [obj.replace(":", "$:") for obj in objects]
            objects += [sycl_devlink_out]
            sycl_devlink_out = sycl_devlink_out.replace(":", "$:")
        else:
            sycl_devlink_objects = list(objects)
            objects += [sycl_devlink_out]
        sycl_devlink_rule = ["rule sycl_devlink"]
        sycl_devlink_rule.append(
            "  command = $sycl $in -o $out $sycl_dlink_post_cflags"
        )
        sycl_devlink = [
            f"build {sycl_devlink_out}: sycl_devlink {' '.join(sycl_devlink_objects)}"
        ]
    else:
        sycl_devlink_rule, sycl_devlink = [], []

    if library_target is not None:
        link_rule = ['rule link']
        if IS_WINDOWS:
            cl_paths = subprocess.check_output(['where',
                                                'cl']).decode(*SUBPROCESS_DECODE_ARGS).split('\r\n')
            if len(cl_paths) >= 1:
                cl_path = os.path.dirname(cl_paths[0]).replace(':', '$:')
            else:
                raise RuntimeError("MSVC is required to load C++ extensions")
            link_rule.append(f'  command = "{cl_path}/link.exe" $in /nologo $ldflags /out:$out')
        else:
            link_rule.append('  command = $cxx $in $ldflags -o $out')

        link = [f'build {library_target}: link {" ".join(objects)}']

        default = [f'default {library_target}']
    else:
        link_rule, link, default = [], [], []

    # 'Blocks' should be separated by newlines, for visual benefit.
    blocks = [config, flags, compile_rule]
    if with_cuda:
        blocks.append(cuda_compile_rule)  # type: ignore[possibly-undefined]
    if with_sycl:
        blocks.append(sycl_compile_rule)  # type: ignore[possibly-undefined]
    blocks += [cuda_devlink_rule, sycl_devlink_rule, link_rule, build, cuda_devlink, sycl_devlink, link, default]
    content = "\n\n".join("\n".join(b) for b in blocks)
    # Ninja requires a new lines at the end of the .ninja file
    content += "\n"
    _maybe_write(path, content)
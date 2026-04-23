def _build_argv(
    tool,
    filename,
    incldirs=None,
    includes=None,
    macros=None,
    preargs=None,
    postargs=None,
    executable=None,
    compiler=None,
):
    if includes:
        includes = tuple(f'-include{i}' for i in includes)
        postargs = (includes + postargs) if postargs else includes

    compiler = distutils.ccompiler.new_compiler(
        compiler=compiler or tool,
    )
    if executable:
        compiler.set_executable('preprocessor', executable)

    argv = None
    def _spawn(_argv):
        nonlocal argv
        argv = _argv
    compiler.spawn = _spawn
    compiler.preprocess(
        filename,
        macros=[tuple(v) for v in macros or ()],
        include_dirs=incldirs or (),
        extra_preargs=preargs or (),
        extra_postargs=postargs or (),
    )
    return argv
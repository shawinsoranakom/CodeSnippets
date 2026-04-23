def compile_c_extension(
    generated_source_path: str,
    build_dir: str | None = None,
    verbose: bool = False,
    keep_asserts: bool = True,
    disable_optimization: bool = False,
    library_dir: str | None = None,
) -> pathlib.Path:
    """Compile the generated source for a parser generator into an extension module.

    The extension module will be generated in the same directory as the provided path
    for the generated source, with the same basename (in addition to extension module
    metadata). For example, for the source mydir/parser.c the generated extension
    in a darwin system with python 3.8 will be mydir/parser.cpython-38-darwin.so.

    If *build_dir* is provided, that path will be used as the temporary build directory
    of distutils (this is useful in case you want to use a temporary directory).

    If *library_dir* is provided, that path will be used as the directory for a
    static library of the common parser sources (this is useful in case you are
    creating multiple extensions).
    """
    import setuptools.command.build_ext
    import setuptools.logging
    from setuptools import Distribution, Extension
    from setuptools._distutils.ccompiler import new_compiler
    from setuptools._distutils.sysconfig import customize_compiler
    from setuptools.modified import newer_group

    if verbose:
        setuptools.logging.set_threshold(logging.DEBUG)

    source_file_path = pathlib.Path(generated_source_path)
    extension_name = source_file_path.stem
    extra_compile_args = get_extra_flags("CFLAGS", "PY_CFLAGS_NODIST")
    extra_compile_args.append("-DPy_BUILD_CORE_MODULE")
    # Define _Py_TEST_PEGEN to not call PyAST_Validate() in Parser/pegen.c
    extra_compile_args.append("-D_Py_TEST_PEGEN")
    if sys.platform == "win32" and sysconfig.get_config_var("Py_GIL_DISABLED"):
        extra_compile_args.append("-DPy_GIL_DISABLED")
    extra_link_args = get_extra_flags("LDFLAGS", "PY_LDFLAGS_NODIST")
    if keep_asserts:
        extra_compile_args.append("-UNDEBUG")
    if disable_optimization:
        if sys.platform == "win32":
            extra_compile_args.append("/Od")
            extra_link_args.append("/LTCG:OFF")
        else:
            extra_compile_args.append("-O0")
            if sysconfig.get_config_var("GNULD") == "yes":
                extra_link_args.append("-fno-lto")

    common_sources = [
        str(MOD_DIR.parent.parent.parent / "Python" / "Python-ast.c"),
        str(MOD_DIR.parent.parent.parent / "Python" / "asdl.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "lexer" / "lexer.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "lexer" / "state.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "lexer" / "buffer.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "tokenizer" / "string_tokenizer.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "tokenizer" / "file_tokenizer.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "tokenizer" / "utf8_tokenizer.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "tokenizer" / "readline_tokenizer.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "tokenizer" / "helpers.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "pegen.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "pegen_errors.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "action_helpers.c"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "string_parser.c"),
        str(MOD_DIR.parent / "peg_extension" / "peg_extension.c"),
    ]
    include_dirs = [
        str(MOD_DIR.parent.parent.parent / "Include" / "internal"),
        str(MOD_DIR.parent.parent.parent / "Include" / "internal" / "mimalloc"),
        str(MOD_DIR.parent.parent.parent / "Parser"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "lexer"),
        str(MOD_DIR.parent.parent.parent / "Parser" / "tokenizer"),
    ]
    if sys.platform == "win32":
        # HACK: The location of pyconfig.h has moved within our build, and
        # setuptools hasn't updated for it yet. So add the path manually for now
        include_dirs.append(pathlib.Path(sysconfig.get_config_h_filename()).parent)
    extension = Extension(
        extension_name,
        sources=[generated_source_path],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
    dist = Distribution({"name": extension_name, "ext_modules": [extension]})
    cmd = dist.get_command_obj("build_ext")
    assert isinstance(cmd, setuptools.command.build_ext.build_ext)
    fixup_build_ext(cmd)
    cmd.build_lib = str(source_file_path.parent)
    cmd.include_dirs = include_dirs
    if build_dir:
        cmd.build_temp = build_dir
    cmd.ensure_finalized()

    compiler = new_compiler()
    customize_compiler(compiler)
    compiler.set_include_dirs(cmd.include_dirs)
    compiler.set_library_dirs(cmd.library_dirs)
    # build static lib
    if library_dir:
        library_filename = compiler.library_filename(extension_name, output_dir=library_dir)
        if newer_group(common_sources, library_filename, "newer"):
            if sys.platform == "win32":
                assert compiler.static_lib_format
                pdb = compiler.static_lib_format % (extension_name, ".pdb")
                compile_opts = [f"/Fd{library_dir}\\{pdb}"]
                compile_opts.extend(extra_compile_args)
            else:
                compile_opts = extra_compile_args
            objects = compiler.compile(
                common_sources,
                output_dir=library_dir,
                debug=cmd.debug,
                extra_postargs=compile_opts,
            )
            compiler.create_static_lib(
                objects, extension_name, output_dir=library_dir, debug=cmd.debug
            )
        if sys.platform == "win32":
            compiler.add_library_dir(library_dir)
            extension.libraries = [extension_name]
        elif sys.platform == "darwin":
            compiler.set_link_objects(
                [
                    "-Wl,-force_load",
                    library_filename,
                ]
            )
        else:
            compiler.set_link_objects(
                [
                    "-Wl,--whole-archive",
                    library_filename,
                    "-Wl,--no-whole-archive",
                ]
            )
    else:
        extension.sources[0:0] = common_sources

    # Compile the source code to object files.
    ext_path = cmd.get_ext_fullpath(extension_name)
    if newer_group(extension.sources, ext_path, "newer"):
        objects = compiler.compile(
            extension.sources,
            output_dir=cmd.build_temp,
            debug=cmd.debug,
            extra_postargs=extra_compile_args,
        )
    else:
        objects = compiler.object_filenames(extension.sources, output_dir=cmd.build_temp)
    # The cmd.get_libraries() call needs a valid compiler attribute or we will
    # get an incorrect library name on the free-threaded Windows build.
    cmd.compiler = compiler
    # Now link the object files together into a "shared object"
    compiler.link_shared_object(
        objects,
        ext_path,
        libraries=cmd.get_libraries(extension),
        extra_postargs=extra_link_args,
        export_symbols=cmd.get_export_symbols(extension),  # type: ignore[no-untyped-call]
        debug=cmd.debug,
        build_temp=cmd.build_temp,
    )

    return pathlib.Path(ext_path)
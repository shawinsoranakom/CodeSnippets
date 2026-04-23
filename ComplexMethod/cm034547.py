def boilerplate_module(modfile, args, interpreters, check, destfile):
    """ simulate what ansible does with new style modules """

    # module_fh = open(modfile)
    # module_data = module_fh.read()
    # module_fh.close()

    # replacer = module_common.ModuleReplacer()
    loader = DataLoader()

    # included_boilerplate = module_data.find(module_common.REPLACER) != -1 or module_data.find("import ansible.module_utils") != -1

    complex_args = {}

    # default selinux fs list is pass in as _ansible_selinux_special_fs arg
    complex_args['_ansible_selinux_special_fs'] = C.DEFAULT_SELINUX_SPECIAL_FS
    complex_args['_ansible_tmpdir'] = C.DEFAULT_LOCAL_TMP
    complex_args['_ansible_keep_remote_files'] = C.DEFAULT_KEEP_REMOTE_FILES
    complex_args['_ansible_version'] = __version__

    if args.startswith("@"):
        # Argument is a YAML file (JSON is a subset of YAML)
        complex_args = utils_vars.combine_vars(complex_args, loader.load_from_file(args[1:]))
        args = ''
    elif args.startswith("{"):
        # Argument is a YAML document (not a file)
        complex_args = utils_vars.combine_vars(complex_args, loader.load(args))
        args = ''

    if args:
        parsed_args = parse_kv(args)
        complex_args = utils_vars.combine_vars(complex_args, parsed_args)

    task_vars = interpreters

    if check:
        complex_args['_ansible_check_mode'] = True

    modfile = os.path.abspath(modfile)
    modname = os.path.basename(modfile)
    modname = os.path.splitext(modname)[0]

    built_module = module_common.modify_module(
        module_name=modname,
        module_path=modfile,
        module_args=complex_args,
        templar=Templar(loader=loader),
        task_vars=task_vars
    )

    module_data, module_style = built_module.b_module_data, built_module.module_style

    if module_style == 'new' and '_ANSIBALLZ_WRAPPER = True' in to_native(module_data):
        module_style = 'ansiballz'

    modfile2_path = os.path.expanduser(destfile)
    print("* including generated source, if any, saving to: %s" % modfile2_path)
    if module_style not in ('ansiballz', 'old'):
        print("* this may offset any line numbers in tracebacks/debuggers!")
    with open(modfile2_path, 'wb') as modfile2:
        modfile2.write(module_data)
    modfile = modfile2_path

    return (modfile2_path, modname, module_style)
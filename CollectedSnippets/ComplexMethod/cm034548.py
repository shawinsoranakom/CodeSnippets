def ansiballz_setup(modfile, modname, interpreters):
    os.system("chmod +x %s" % modfile)

    if 'ansible_python_interpreter' in interpreters:
        command = [interpreters['ansible_python_interpreter']]
    else:
        command = []
    command.extend([modfile, 'explode'])

    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = cmd.communicate()
    out, err = to_text(out, errors='surrogate_or_strict'), to_text(err)
    lines = out.splitlines()
    if len(lines) != 2 or 'Module expanded into' not in lines[0]:
        print("*" * 35)
        print("INVALID OUTPUT FROM ANSIBALLZ MODULE WRAPPER")
        print(out)
        sys.exit(err)
    debug_dir = lines[1].strip()

    # All the directories in an AnsiBallZ that modules can live
    core_dirs = glob.glob(os.path.join(debug_dir, 'ansible/modules'))
    non_core_dirs = glob.glob(os.path.join(debug_dir, 'ansible/legacy'))
    collection_dirs = glob.glob(os.path.join(debug_dir, 'ansible_collections/*/*/plugins/modules'))

    # There's only one module in an AnsiBallZ payload so look for the first module and then exit
    for module_dir in core_dirs + collection_dirs + non_core_dirs:
        for dirname, directories, filenames in os.walk(module_dir):
            for filename in filenames:
                if filename == modname + '.py':
                    modfile = os.path.join(dirname, filename)
                    break

    argsfile = os.path.join(debug_dir, 'args')

    print("* ansiballz module detected; extracted module source to: %s" % debug_dir)
    return modfile, argsfile
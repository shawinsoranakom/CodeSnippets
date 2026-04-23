def get_extension_defn(moduleName, mapFileName, prefix):
    if win32api is None: return None
    os.environ['PYTHONPREFIX'] = prefix
    dsp = win32api.GetProfileVal(moduleName, "dsp", "", mapFileName)
    if dsp=="":
        return None

    # We allow environment variables in the file name
    dsp = win32api.ExpandEnvironmentStrings(dsp)
    # If the path to the .DSP file is not absolute, assume it is relative
    # to the description file.
    if not os.path.isabs(dsp):
        dsp = os.path.join( os.path.split(mapFileName)[0], dsp)
    # Parse it to extract the source files.
    sourceFiles = parse_dsp(dsp)
    if sourceFiles is None:
        return None

    module = CExtension(moduleName, sourceFiles)
    # Put the path to the DSP into the environment so entries can reference it.
    os.environ['dsp_path'] = os.path.split(dsp)[0]
    os.environ['ini_path'] = os.path.split(mapFileName)[0]

    cl_options = win32api.GetProfileVal(moduleName, "cl", "", mapFileName)
    if cl_options:
        module.AddCompilerOption(win32api.ExpandEnvironmentStrings(cl_options))

    exclude = win32api.GetProfileVal(moduleName, "exclude", "", mapFileName)
    exclude = exclude.split()

    if win32api.GetProfileVal(moduleName, "Unicode", 0, mapFileName):
        module.AddCompilerOption('/D UNICODE /D _UNICODE')

    libs = win32api.GetProfileVal(moduleName, "libs", "", mapFileName).split()
    for lib in libs:
        module.AddLinkerLib(win32api.ExpandEnvironmentStrings(lib))

    for exc in exclude:
        if exc in module.sourceFiles:
            module.sourceFiles.remove(exc)

    return module
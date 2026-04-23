def list_scripts(scriptdirname, extension, *, include_extensions=True):
    scripts = {}

    loaded_extensions = {ext.canonical_name: ext for ext in extensions.active()}
    loaded_extensions_scripts = {ext.canonical_name: [] for ext in extensions.active()}

    # build script dependency map
    root_script_basedir = os.path.join(paths.script_path, scriptdirname)
    if os.path.exists(root_script_basedir):
        for filename in sorted(os.listdir(root_script_basedir)):
            if not os.path.isfile(os.path.join(root_script_basedir, filename)):
                continue

            if os.path.splitext(filename)[1].lower() != extension:
                continue

            script_file = ScriptFile(paths.script_path, filename, os.path.join(root_script_basedir, filename))
            scripts[filename] = ScriptWithDependencies(filename, script_file, [], [], [])

    if include_extensions:
        for ext in extensions.active():
            extension_scripts_list = ext.list_files(scriptdirname, extension)
            for extension_script in extension_scripts_list:
                if not os.path.isfile(extension_script.path):
                    continue

                script_canonical_name = ("builtin/" if ext.is_builtin else "") + ext.canonical_name + "/" + extension_script.filename
                relative_path = scriptdirname + "/" + extension_script.filename

                script = ScriptWithDependencies(
                    script_canonical_name=script_canonical_name,
                    file=extension_script,
                    requires=ext.metadata.get_script_requirements("Requires", relative_path, scriptdirname),
                    load_before=ext.metadata.get_script_requirements("Before", relative_path, scriptdirname),
                    load_after=ext.metadata.get_script_requirements("After", relative_path, scriptdirname),
                )

                scripts[script_canonical_name] = script
                loaded_extensions_scripts[ext.canonical_name].append(script)

    for script_canonical_name, script in scripts.items():
        # load before requires inverse dependency
        # in this case, append the script name into the load_after list of the specified script
        for load_before in script.load_before:
            # if this requires an individual script to be loaded before
            other_script = scripts.get(load_before)
            if other_script:
                other_script.load_after.append(script_canonical_name)

            # if this requires an extension
            other_extension_scripts = loaded_extensions_scripts.get(load_before)
            if other_extension_scripts:
                for other_script in other_extension_scripts:
                    other_script.load_after.append(script_canonical_name)

        # if After mentions an extension, remove it and instead add all of its scripts
        for load_after in list(script.load_after):
            if load_after not in scripts and load_after in loaded_extensions_scripts:
                script.load_after.remove(load_after)

                for other_script in loaded_extensions_scripts.get(load_after, []):
                    script.load_after.append(other_script.script_canonical_name)

    dependencies = {}

    for script_canonical_name, script in scripts.items():
        for required_script in script.requires:
            if required_script not in scripts and required_script not in loaded_extensions:
                errors.report(f'Script "{script_canonical_name}" requires "{required_script}" to be loaded, but it is not.', exc_info=False)

        dependencies[script_canonical_name] = script.load_after

    ordered_scripts = topological_sort(dependencies)
    scripts_list = [scripts[script_canonical_name].file for script_canonical_name in ordered_scripts]

    return scripts_list
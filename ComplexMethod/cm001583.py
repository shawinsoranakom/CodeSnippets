def list_extensions():
    extensions.clear()
    extension_paths.clear()
    loaded_extensions.clear()

    if shared.cmd_opts.disable_all_extensions:
        print("*** \"--disable-all-extensions\" arg was used, will not load any extensions ***")
    elif shared.opts.disable_all_extensions == "all":
        print("*** \"Disable all extensions\" option was set, will not load any extensions ***")
    elif shared.cmd_opts.disable_extra_extensions:
        print("*** \"--disable-extra-extensions\" arg was used, will only load built-in extensions ***")
    elif shared.opts.disable_all_extensions == "extra":
        print("*** \"Disable all extensions\" option was set, will only load built-in extensions ***")


    # scan through extensions directory and load metadata
    for dirname in [extensions_builtin_dir, extensions_dir]:
        if not os.path.isdir(dirname):
            continue

        for extension_dirname in sorted(os.listdir(dirname)):
            path = os.path.join(dirname, extension_dirname)
            if not os.path.isdir(path):
                continue

            canonical_name = extension_dirname
            metadata = ExtensionMetadata(path, canonical_name)

            # check for duplicated canonical names
            already_loaded_extension = loaded_extensions.get(metadata.canonical_name)
            if already_loaded_extension is not None:
                errors.report(f'Duplicate canonical name "{canonical_name}" found in extensions "{extension_dirname}" and "{already_loaded_extension.name}". Former will be discarded.', exc_info=False)
                continue

            is_builtin = dirname == extensions_builtin_dir
            extension = Extension(name=extension_dirname, path=path, enabled=extension_dirname not in shared.opts.disabled_extensions, is_builtin=is_builtin, metadata=metadata)
            extensions.append(extension)
            extension_paths[extension.path] = extension
            loaded_extensions[canonical_name] = extension

    for extension in extensions:
        extension.metadata.requires = extension.metadata.get_script_requirements("Requires", "Extension")

    # check for requirements
    for extension in extensions:
        if not extension.enabled:
            continue

        for req in extension.metadata.requires:
            required_extension = loaded_extensions.get(req)
            if required_extension is None:
                errors.report(f'Extension "{extension.name}" requires "{req}" which is not installed.', exc_info=False)
                continue

            if not required_extension.enabled:
                errors.report(f'Extension "{extension.name}" requires "{required_extension.name}" which is disabled.', exc_info=False)
                continue
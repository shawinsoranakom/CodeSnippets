def sanitize_filename(
    filename: str,
    modules: t.Optional[dict[str, str]] = None,
    collection_search_re: t.Optional[t.Pattern] = None,
    collection_sub_re: t.Optional[t.Pattern] = None,
) -> t.Optional[str]:
    """Convert the given code coverage path to a local absolute path and return its, or None if the path is not valid."""
    ansible_path = os.path.abspath('lib/ansible/') + '/'
    root_path = data_context().content.root + '/'
    integration_temp_path = os.path.sep + os.path.join(ResultType.TMP.relative_path, 'integration') + os.path.sep

    if modules is None:
        modules = {}

    if '/ansible_modlib.zip/ansible/' in filename:
        # Rewrite the module_utils path from the remote host to match the controller. Ansible 2.6 and earlier.
        new_name = re.sub('^.*/ansible_modlib.zip/ansible/', ansible_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif integration_temp_path in filename:
        # Rewrite the path of code running from an integration test temporary directory.
        new_name = re.sub(r'^.*' + re.escape(integration_temp_path) + '[^/]+/', root_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif collection_search_re and collection_search_re.search(filename):
        new_name = os.path.abspath(collection_sub_re.sub('', filename))
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search(r'/ansible_[^/]+_payload\.zip/ansible/', filename):
        # Rewrite the module_utils path from the remote host to match the controller. Ansible 2.7 and later.
        new_name = re.sub(r'^.*/ansible_[^/]+_payload\.zip/ansible/', ansible_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif '/ansible_module_' in filename:
        # Rewrite the module path from the remote host to match the controller. Ansible 2.6 and earlier.
        module_name = re.sub('^.*/ansible_module_(?P<module>.*).py$', '\\g<module>', filename)
        if module_name not in modules:
            display.warning('Skipping coverage of unknown module: %s' % module_name)
            return None
        new_name = os.path.abspath(modules[module_name])
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search(r'/ansible_[^/]+_payload(_[^/]+|\.zip)/__main__\.py$', filename):
        # Rewrite the module path from the remote host to match the controller. Ansible 2.7 and later.
        # AnsiballZ versions using zipimporter will match the `.zip` portion of the regex.
        # AnsiballZ versions not using zipimporter will match the `_[^/]+` portion of the regex.
        module_name = re.sub(r'^.*/ansible_(?P<module>[^/]+)_payload(_[^/]+|\.zip)/__main__\.py$',
                             '\\g<module>', filename).rstrip('_')
        if module_name not in modules:
            display.warning('Skipping coverage of unknown module: %s' % module_name)
            return None
        new_name = os.path.abspath(modules[module_name])
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search('^(/.*?)?/root/ansible/', filename):
        # Rewrite the path of code running on a remote host or in a docker container as root.
        new_name = re.sub('^(/.*?)?/root/ansible/', root_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name

    filename = os.path.abspath(filename)  # make sure path is absolute (will be relative if previously exported)

    return filename
def read_docstring_from_python_file(filename, verbose=True, ignore_errors=True):
    """
    Use ast to search for assignment of the DOCUMENTATION and EXAMPLES variables in the given file.
    Parse DOCUMENTATION from YAML and return the YAML doc or None together with EXAMPLES, as plain text.
    """
    data = _init_doc_dict()

    try:
        with open(filename, 'rb') as b_module_data:
            M = ast.parse(b_module_data.read())

        for child in M.body:
            if isinstance(child, ast.Assign):
                for t in child.targets:
                    try:
                        theid = t.id
                    except AttributeError:
                        # skip errors can happen when trying to use the normal code
                        display.warning("Building documentation, failed to assign id for %s on %s, skipping" % (t, filename))
                        continue

                    if theid in string_to_vars:
                        varkey = string_to_vars[theid]
                        if isinstance(child.value, ast.Dict):
                            data[varkey] = ast.literal_eval(child.value)
                        else:
                            if theid == 'EXAMPLES':
                                # examples 'can' be yaml, but even if so, we dont want to parse as such here
                                # as it can create undesired 'objects' that don't display well as docs.
                                data[varkey] = to_text(child.value.value)
                            else:
                                # string should be yaml if already not a dict
                                child_value = _tags.Origin(path=filename, line_num=child.value.lineno).tag(child.value.value)
                                data[varkey] = yaml.load(child_value, Loader=AnsibleLoader)

                        display.debug('Documentation assigned: %s' % varkey)

    except Exception as ex:
        msg = f"Unable to parse documentation in python file {filename!r}"
        # DTFIX-FUTURE: better pattern to conditionally raise/display
        if not ignore_errors:
            raise AnsibleParserError(f'{msg}.') from ex
        elif verbose:
            display.error(f'{msg}: {ex}.')

    return data
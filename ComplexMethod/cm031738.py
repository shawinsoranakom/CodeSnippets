def run_clinic(parser: argparse.ArgumentParser, ns: argparse.Namespace) -> None:
    if ns.converters:
        if ns.filename:
            parser.error(
                "can't specify --converters and a filename at the same time"
            )
        AnyConverterType = ConverterType | ReturnConverterType
        converter_list: list[tuple[str, AnyConverterType]] = []
        return_converter_list: list[tuple[str, AnyConverterType]] = []

        for name, converter in converters.items():
            converter_list.append((
                name,
                converter,
            ))
        for name, return_converter in return_converters.items():
            return_converter_list.append((
                name,
                return_converter
            ))

        print()

        print("Legacy converters:")
        legacy = sorted(legacy_converters)
        print('    ' + ' '.join(c for c in legacy if c[0].isupper()))
        print('    ' + ' '.join(c for c in legacy if c[0].islower()))
        print()

        for title, attribute, ids in (
            ("Converters", 'converter_init', converter_list),
            ("Return converters", 'return_converter_init', return_converter_list),
        ):
            print(title + ":")

            ids.sort(key=lambda item: item[0].lower())
            longest = -1
            for name, _ in ids:
                longest = max(longest, len(name))

            for name, cls in ids:
                callable = getattr(cls, attribute, None)
                if not callable:
                    continue
                signature = inspect.signature(callable)
                parameters = []
                for parameter_name, parameter in signature.parameters.items():
                    if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                        if parameter.default != inspect.Parameter.empty:
                            s = f'{parameter_name}={parameter.default!r}'
                        else:
                            s = parameter_name
                        parameters.append(s)
                print('    {}({})'.format(name, ', '.join(parameters)))
            print()
        print("All converters also accept (c_default=None, py_default=None, annotation=None).")
        print("All return converters also accept (py_default=None).")
        return

    if ns.make:
        if ns.output or ns.filename:
            parser.error("can't use -o or filenames with --make")
        if not ns.srcdir:
            parser.error("--srcdir must not be empty with --make")
        if ns.exclude:
            excludes = [os.path.join(ns.srcdir, f) for f in ns.exclude]
            excludes = [os.path.normpath(f) for f in excludes]
        else:
            excludes = []
        for root, dirs, files in os.walk(ns.srcdir):
            for rcs_dir in ('.svn', '.git', '.hg', 'build', 'externals'):
                if rcs_dir in dirs:
                    dirs.remove(rcs_dir)
            for filename in files:
                # handle .c, .cpp and .h files
                if not filename.endswith(('.c', '.cpp', '.h')):
                    continue
                path = os.path.join(root, filename)
                path = os.path.normpath(path)
                if path in excludes:
                    continue
                if ns.verbose:
                    print(path)
                parse_file(path,
                           verify=not ns.force, limited_capi=ns.limited_capi)
        return

    if not ns.filename:
        parser.error("no input files")

    if ns.output and len(ns.filename) > 1:
        parser.error("can't use -o with multiple filenames")

    for filename in ns.filename:
        if ns.verbose:
            print(filename)
        parse_file(filename, output=ns.output,
                   verify=not ns.force, limited_capi=ns.limited_capi)
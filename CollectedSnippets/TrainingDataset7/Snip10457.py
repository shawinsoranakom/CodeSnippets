def serialize_deconstructed(path, args, kwargs):
        name, imports = DeconstructibleSerializer._serialize_path(path)
        strings = []
        for arg in args:
            arg_string, arg_imports = serializer_factory(arg).serialize()
            strings.append(arg_string)
            imports.update(arg_imports)
        non_ident_kwargs = {}
        for kw, arg in sorted(kwargs.items()):
            if kw.isidentifier():
                arg_string, arg_imports = serializer_factory(arg).serialize()
                imports.update(arg_imports)
                strings.append("%s=%s" % (kw, arg_string))
            else:
                non_ident_kwargs[kw] = arg
        if non_ident_kwargs:
            # Serialize non-identifier keyword arguments as a dict.
            kw_string, kw_imports = serializer_factory(non_ident_kwargs).serialize()
            strings.append(f"**{kw_string}")
            imports.update(kw_imports)

        return "%s(%s)" % (name, ", ".join(strings)), imports
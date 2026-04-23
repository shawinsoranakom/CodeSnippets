def _fn_to_stable_annotation_str(self, obj):
        """
        Unfortunately we have to serialize function signatures manually since
        serialization for `inspect.Signature` objects is not stable across
        python versions
        """
        fn_name = torch.typename(obj)

        signature = inspect.signature(obj)

        sig_str = f"{fn_name}{signature}"

        arg_strs = []
        for k, v in signature.parameters.items():
            maybe_type_annotation = (
                f": {self._annotation_type_to_stable_str(v.annotation, sig_str)}"
                if v.annotation is not inspect.Signature.empty
                else ""
            )

            def default_val_str(val):
                if isinstance(val, (tuple, list)):
                    str_pieces = ["(" if isinstance(val, tuple) else "["]
                    str_pieces.append(", ".join(default_val_str(v) for v in val))
                    if isinstance(val, tuple) and len(str_pieces) == 2:
                        str_pieces.append(",")
                    str_pieces.append(")" if isinstance(val, tuple) else "]")
                    return "".join(str_pieces)

                # Need to fix up some default value strings.
                # First case: modules. Default module `repr` contains the FS path of the module.
                # Don't leak that
                if isinstance(val, types.ModuleType):
                    return f"<module {val.__name__}>"

                # Second case: callables. Callables (such as lambdas) encode their address in
                # their string repr. Don't do that
                if callable(val):
                    return f"<function {val.__name__}>"

                return str(val)

            if v.default is not inspect.Signature.empty:
                default_val_str = (
                    default_val_str(v.default)
                    if not isinstance(v.default, str)
                    else f"'{v.default}'"
                )
                maybe_default = f" = {default_val_str}"
            else:
                maybe_default = ""
            maybe_stars = ""
            if v.kind == inspect.Parameter.VAR_POSITIONAL:
                maybe_stars = "*"
            elif v.kind == inspect.Parameter.VAR_KEYWORD:
                maybe_stars = "**"
            arg_strs.append(f"{maybe_stars}{k}{maybe_type_annotation}{maybe_default}")

        return_annot = (
            f" -> {self._annotation_type_to_stable_str(signature.return_annotation, sig_str)}"
            if signature.return_annotation is not inspect.Signature.empty
            else ""
        )

        return f'{fn_name}({", ".join(arg_strs)}){return_annot}'
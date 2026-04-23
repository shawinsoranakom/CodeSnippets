def _visit(obj: Any, path: Any):
                    if isinstance(obj, dict) and "Ref" in obj:
                        ref_variable = obj["Ref"]
                        if ref_variable == iteration_name:
                            return variable
                    elif isinstance(obj, dict) and "Fn::Sub" in obj:
                        arguments = recurse_object(obj["Fn::Sub"], _visit)
                        if isinstance(arguments, str):
                            # simple case
                            # TODO: can this reference anything outside of the template?
                            result = arguments
                            variables_found = re.findall("\\${([^}]+)}", arguments)
                            for var in variables_found:
                                if var == iteration_name:
                                    result = result.replace(f"${{{var}}}", variable)
                            return result
                        else:
                            raise NotImplementedError
                    elif isinstance(obj, dict) and "Fn::Join" in obj:
                        # first visit arguments
                        arguments = recurse_object(
                            obj["Fn::Join"],
                            _visit,
                        )
                        separator, items = arguments
                        return separator.join(items)
                    return obj
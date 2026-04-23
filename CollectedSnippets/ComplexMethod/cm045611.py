def _is_deletion_put(self, node: ast.Call) -> bool:
            try:
                # self._buffer.put(...)
                if not (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == self.PUT_METHOD_NAME
                ):
                    return False

                buf = node.func.value
                if not (
                    isinstance(buf, ast.Attribute)
                    and isinstance(buf.value, ast.Name)
                    and buf.value.id == self.SELF_IDENTIFIER
                    and buf.attr == self.BUFFER_NAME
                ):
                    return False

                # args[0] exists and is a tuple
                if not node.args:
                    return False

                first = node.args[0]
                if not isinstance(first, ast.Tuple) or not first.elts:
                    return False

                # first element == PythonConnectorEventType.DELETE
                elt = first.elts[0]
                if not isinstance(elt, ast.Attribute):
                    return False

                if isinstance(elt.value, ast.Name):
                    maybe_enum_name = elt.value.id
                elif isinstance(elt.value, ast.Attribute):
                    maybe_enum_name = elt.value.attr
                else:
                    return False
                maybe_enum_variant = elt.attr

                return (
                    maybe_enum_name == PythonConnectorEventType.__name__
                    and maybe_enum_variant == PythonConnectorEventType.DELETE.name
                )
            except (AttributeError, IndexError):
                return False
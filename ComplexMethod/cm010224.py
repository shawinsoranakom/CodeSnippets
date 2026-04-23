def dump_field(f) -> tuple[dict[str, Any], str, str | None, str, int]:
            t, cpp_type, thrift_type = dump_type(f.type, 0)
            ret = {"type": t}
            cpp_default: str | None = None
            if typing.get_origin(f.type) is not Annotated:
                raise AssertionError(
                    f"Field {f.name} must be annotated with an integer id."
                )
            thrift_id = f.type.__metadata__[0]
            if type(thrift_id) is not int:
                raise AssertionError(
                    f"Field {f.name} must be annotated with an integer id, got {type(thrift_id)}"
                )

            value = dataclasses.MISSING
            if f.default is not dataclasses.MISSING:
                value = f.default
            elif f.default_factory is not dataclasses.MISSING:
                value = f.default_factory()

            if value is not dataclasses.MISSING:
                default = str(value)
                ret["default"] = default
                cpp_default = dump_cpp_value(value)

                if t.startswith("Optional[") and value is not None:
                    raise AssertionError(
                        f"Optional field {ty.__name__}.{f.name} must have default value to be None."
                    )

            return ret, cpp_type, cpp_default, thrift_type, thrift_id
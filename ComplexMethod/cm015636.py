def fn(obj):
            class_fields = dataclasses.fields(obj)
            assert len(class_fields)  # noqa: S101
            assert all(field.default is None for field in class_fields[1:])  # noqa: S101
            other_fields_are_none = all(
                getattr(obj, field.name) is None for field in class_fields[1:]
            )
            assert not other_fields_are_none  # noqa: S101

            if not hasattr(obj, "a"):
                return -1
            if hasattr(obj, "z"):
                return -2

            total = getattr(obj, class_fields[0].name)
            for field in class_fields[1:]:
                v = getattr(obj, field.name)
                if v is not None:
                    total += v

            return total
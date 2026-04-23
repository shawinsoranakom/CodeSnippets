def test_views_op_having_view_copy(self) -> None:
        schemas = torch._C._dispatch_get_registrations_for_dispatch_key("")
        aten_schemas = [s[6:] for s in schemas if s.startswith("aten::")]

        for aten_schema in aten_schemas:
            val = aten_schema.split(".")
            if len(val) > 2:
                raise AssertionError(f"Expected at most 2 parts, got {len(val)}: {val}")
            name = ""
            overload = ""
            if len(val) == 1:
                name = val[0]
                overload = "default"
            else:
                name, overload = val[0], val[1]

            op_overload = getattr(getattr(torch.ops.aten, name), overload)
            if torch.Tag.core in op_overload.tags and is_view_op(op_overload._schema):
                self.assertIsNotNone(get_view_copy_of_view_op(op_overload._schema))
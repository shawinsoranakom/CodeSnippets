def test_equality_respects_static_attributes(self):
        def _get_sample_op_schemas(static_arg_val, static_kwarg_val):
            dts = DTensorSpec(mesh=None, placements=tuple(), tensor_meta=None)
            static_argnum = 2
            static_kwargkey = ["statickwarg"]
            annotated_schemas = [
                (False, False, None),
                (True, False, RuntimeSchemaInfo(static_argnum=static_argnum)),
                (False, True, RuntimeSchemaInfo(static_kwargkey=static_kwargkey)),
                (
                    True,
                    True,
                    RuntimeSchemaInfo(
                        static_argnum=static_argnum, static_kwargkey=static_kwargkey
                    ),
                ),
            ]

            # non-tensor args show up in hash iff the argnum is static/
            # kwargs show up in hash iff their name is in static_kwargkey.
            # random elements are random because they are not supposed to matter for
            # equality at all.
            args_schema = (dts, random.randint(1, 1000000), static_arg_val)
            kwargs_schema = {
                "ignoredkwarg": random.randint(1, 1000000),
                "statickwarg": static_kwarg_val,
            }
            return [
                (
                    has_static_arg,
                    has_static_kwarg,
                    OpSchema(
                        op=None,
                        args_schema=args_schema,
                        kwargs_schema=kwargs_schema,
                        schema_info=si,
                    ),
                )
                for (has_static_arg, has_static_kwarg, si) in annotated_schemas
            ]

        for lhs_has_static_arg, lhs_has_static_kwarg, lhs in _get_sample_op_schemas(
            1, 2
        ):
            # Static arg/kwarg both match
            for rhs_has_static_arg, rhs_has_static_kwarg, rhs in _get_sample_op_schemas(
                1, 2
            ):
                if (
                    lhs_has_static_arg == rhs_has_static_arg
                    and lhs_has_static_kwarg == rhs_has_static_kwarg
                ):
                    self.assertEqual(lhs, rhs)
                else:
                    self.assertNotEqual(lhs, rhs)

            # Static arg mismatch
            for rhs_has_static_arg, rhs_has_static_kwarg, rhs in _get_sample_op_schemas(
                3, 2
            ):
                if (
                    lhs_has_static_arg
                    or rhs_has_static_arg
                    or lhs_has_static_kwarg != rhs_has_static_kwarg
                ):
                    self.assertNotEqual(lhs, rhs)
                else:
                    self.assertEqual(lhs, rhs)

            # Static kwarg mismatch
            for rhs_has_static_arg, rhs_has_static_kwarg, rhs in _get_sample_op_schemas(
                1, 3
            ):
                if (
                    lhs_has_static_kwarg
                    or rhs_has_static_kwarg
                    or lhs_has_static_arg != rhs_has_static_arg
                ):
                    self.assertNotEqual(lhs, rhs)
                else:
                    self.assertEqual(lhs, rhs)

            # Static arg/kwarg both mismatch
            for rhs_has_static_arg, rhs_has_static_kwarg, rhs in _get_sample_op_schemas(
                3, 4
            ):
                if (
                    lhs_has_static_arg
                    or rhs_has_static_arg
                    or lhs_has_static_kwarg
                    or rhs_has_static_kwarg
                ):
                    self.assertNotEqual(lhs, rhs)
                else:
                    self.assertEqual(lhs, rhs)
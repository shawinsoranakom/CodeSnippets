def test_keyword_only_args_signature(self):
        operation = (
            custom_migration_operations.operations.ArgsAndKeywordOnlyArgsOperation(
                1, 2, kwarg1=3, kwarg2=4
            )
        )
        buff, imports = OperationWriter(operation, indentation=0).serialize()
        self.assertEqual(imports, {"import custom_migration_operations.operations"})
        self.assertEqual(
            buff,
            "custom_migration_operations.operations.ArgsAndKeywordOnlyArgsOperation(\n"
            "    arg1=1,\n"
            "    arg2=2,\n"
            "    kwarg1=3,\n"
            "    kwarg2=4,\n"
            "),",
        )
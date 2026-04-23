def assertFormatterFailureCaught(
        self, *args, module="migrations.test_migrations", **kwargs
    ):
        with (
            self.temporary_migration_module(module=module),
            AssertFormatterFailureCaughtContext(self) as ctx,
        ):
            call_command(*args, stdout=ctx.stdout, stderr=ctx.stderr, **kwargs)
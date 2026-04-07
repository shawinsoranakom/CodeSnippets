def test_migrations_only(self):
        """
        If all apps have migrations, migration signals should be sent.
        """
        pre_migrate_receiver = Receiver(signals.pre_migrate)
        post_migrate_receiver = Receiver(signals.post_migrate)
        management.call_command(
            "migrate",
            database=MIGRATE_DATABASE,
            verbosity=MIGRATE_VERBOSITY,
            interactive=MIGRATE_INTERACTIVE,
        )
        for receiver in [pre_migrate_receiver, post_migrate_receiver]:
            args = receiver.call_args
            self.assertEqual(receiver.call_counter, 1)
            self.assertEqual(set(args), set(SIGNAL_ARGS))
            self.assertEqual(args["app_config"], APP_CONFIG)
            self.assertEqual(args["verbosity"], MIGRATE_VERBOSITY)
            self.assertEqual(args["interactive"], MIGRATE_INTERACTIVE)
            self.assertEqual(args["using"], "default")
            self.assertIsInstance(args["plan"][0][0], migrations.Migration)
            # The migration isn't applied backward.
            self.assertFalse(args["plan"][0][1])
            self.assertIsInstance(args["apps"], migrations.state.StateApps)
        self.assertEqual(pre_migrate_receiver.call_args["apps"].get_models(), [])
        self.assertEqual(
            [
                model._meta.label
                for model in post_migrate_receiver.call_args["apps"].get_models()
            ],
            ["migrate_signals.Signal"],
        )
        # Migrating with an empty plan.
        pre_migrate_receiver = Receiver(signals.pre_migrate)
        post_migrate_receiver = Receiver(signals.post_migrate)
        management.call_command(
            "migrate",
            database=MIGRATE_DATABASE,
            verbosity=MIGRATE_VERBOSITY,
            interactive=MIGRATE_INTERACTIVE,
        )
        self.assertEqual(
            [
                model._meta.label
                for model in pre_migrate_receiver.call_args["apps"].get_models()
            ],
            ["migrate_signals.Signal"],
        )
        self.assertEqual(
            [
                model._meta.label
                for model in post_migrate_receiver.call_args["apps"].get_models()
            ],
            ["migrate_signals.Signal"],
        )
        # Migrating with an empty plan and --check doesn't emit signals.
        pre_migrate_receiver = Receiver(signals.pre_migrate)
        post_migrate_receiver = Receiver(signals.post_migrate)
        management.call_command(
            "migrate",
            database=MIGRATE_DATABASE,
            verbosity=MIGRATE_VERBOSITY,
            interactive=MIGRATE_INTERACTIVE,
            check_unapplied=True,
        )
        self.assertEqual(pre_migrate_receiver.call_counter, 0)
        self.assertEqual(post_migrate_receiver.call_counter, 0)
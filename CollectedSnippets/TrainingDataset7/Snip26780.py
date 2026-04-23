def test_args(self):
        pre_migrate_receiver = Receiver(signals.pre_migrate)
        post_migrate_receiver = Receiver(signals.post_migrate)
        management.call_command(
            "migrate",
            database=MIGRATE_DATABASE,
            verbosity=MIGRATE_VERBOSITY,
            interactive=MIGRATE_INTERACTIVE,
            stdout=StringIO("test_args"),
        )

        for receiver in [pre_migrate_receiver, post_migrate_receiver]:
            with self.subTest(receiver=receiver):
                args = receiver.call_args
                self.assertEqual(receiver.call_counter, 1)
                self.assertEqual(set(args), set(SIGNAL_ARGS))
                self.assertEqual(args["app_config"], APP_CONFIG)
                self.assertEqual(args["verbosity"], MIGRATE_VERBOSITY)
                self.assertEqual(args["interactive"], MIGRATE_INTERACTIVE)
                self.assertEqual(args["using"], "default")
                self.assertIn("test_args", args["stdout"].getvalue())
                self.assertEqual(args["plan"], [])
                self.assertIsInstance(args["apps"], migrations.state.StateApps)
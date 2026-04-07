def test_cancelled(self):
        self.run_collectstatic()
        with mock.patch("builtins.input", side_effect=lambda _: "no"):
            with self.assertRaisesMessage(
                CommandError, "Collecting static files cancelled"
            ):
                call_command("collectstatic", interactive=True)
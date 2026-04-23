def test_non_zero_exit_status_when_path_to_db_is_path(self):
        sqlite_with_path = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path("test.db.sqlite3"),
        }
        cmd_args = self.settings_to_cmd_args_env(sqlite_with_path)[0]

        msg = '"sqlite3 test.db.sqlite3" returned non-zero exit status 1.'
        with (
            mock.patch(
                "django.db.backends.sqlite3.client.DatabaseClient.runshell",
                side_effect=subprocess.CalledProcessError(returncode=1, cmd=cmd_args),
            ),
            self.assertRaisesMessage(CommandError, msg),
        ):
            call_command("dbshell")
def test_makemessages_gettext_version(self, mocked_popen_wrapper):
        # "Normal" output:
        mocked_popen_wrapper.return_value = (
            "xgettext (GNU gettext-tools) 0.18.1\n"
            "Copyright (C) 1995-1998, 2000-2010 Free Software Foundation, Inc.\n"
            "License GPLv3+: GNU GPL version 3 or later "
            "<http://gnu.org/licenses/gpl.html>\n"
            "This is free software: you are free to change and redistribute it.\n"
            "There is NO WARRANTY, to the extent permitted by law.\n"
            "Written by Ulrich Drepper.\n",
            "",
            0,
        )
        cmd = MakeMessagesCommand()
        self.assertEqual(cmd.gettext_version, (0, 18, 1))

        # Version number with only 2 parts (#23788)
        mocked_popen_wrapper.return_value = (
            "xgettext (GNU gettext-tools) 0.17\n",
            "",
            0,
        )
        cmd = MakeMessagesCommand()
        self.assertEqual(cmd.gettext_version, (0, 17))

        # Bad version output
        mocked_popen_wrapper.return_value = ("any other return value\n", "", 0)
        cmd = MakeMessagesCommand()
        with self.assertRaisesMessage(
            CommandError, "Unable to get gettext version. Is it installed?"
        ):
            cmd.gettext_version
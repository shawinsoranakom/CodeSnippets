def assertButtonsDisabled(
        self,
        mode,
        field_name,
        choose_btn_disabled=False,
        remove_btn_disabled=False,
        choose_all_btn_disabled=False,
        remove_all_btn_disabled=False,
    ):
        choose_button = "#id_%s_add" % field_name
        choose_all_button = "#id_%s_add_all" % field_name
        remove_button = "#id_%s_remove" % field_name
        remove_all_button = "#id_%s_remove_all" % field_name
        self.assertEqual(self.is_disabled(choose_button), choose_btn_disabled)
        self.assertEqual(self.is_disabled(remove_button), remove_btn_disabled)
        if mode == "horizontal":
            self.assertEqual(
                self.is_disabled(choose_all_button), choose_all_btn_disabled
            )
            self.assertEqual(
                self.is_disabled(remove_all_button), remove_all_btn_disabled
            )
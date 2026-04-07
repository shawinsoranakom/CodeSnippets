def test_bug_14242(self):
        # A regression test, introduce by adding an optimization for the
        # UserChangeForm.

        class MyUserForm(UserChangeForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["groups"].help_text = (
                    "These groups give users different permissions"
                )

            class Meta(UserChangeForm.Meta):
                fields = ("groups",)

        # Just check we can create it
        MyUserForm({})
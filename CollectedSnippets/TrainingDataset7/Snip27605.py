def test_rename_field(self):
        project_state = self.get_base_project_state()
        field = project_state.models["tests", "comment"].fields["user"]
        self.assertEqual(
            project_state.relations["tests", "user"]["tests", "comment"],
            {"user": field},
        )

        project_state.rename_field("tests", "comment", "user", "author")
        renamed_field = project_state.models["tests", "comment"].fields["author"]
        self.assertEqual(
            project_state.relations["tests", "user"]["tests", "comment"],
            {"author": renamed_field},
        )
        self.assertEqual(field, renamed_field)
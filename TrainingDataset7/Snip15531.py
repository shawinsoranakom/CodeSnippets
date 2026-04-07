def test_inlines_based_on_model_state(self):
        parent = ShowInlineParent.objects.create(show_inlines=False)
        data = {
            "show_inlines": "on",
            "_save": "Save",
        }
        change_url = reverse(
            "admin:admin_inlines_showinlineparent_change",
            args=(parent.id,),
        )
        response = self.client.post(change_url, data)
        self.assertEqual(response.status_code, 302)
        parent.refresh_from_db()
        self.assertIs(parent.show_inlines, True)
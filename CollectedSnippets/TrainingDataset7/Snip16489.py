def test_changelist_input_html(self):
        response = self.client.get(reverse("admin:admin_views_person_changelist"))
        # 2 inputs per object(the field and the hidden id field) = 6
        # 4 management hidden fields = 4
        # 4 action inputs (3 regular checkboxes, 1 checkbox to select all)
        # main form submit button = 1
        # search field and search submit button = 2
        # CSRF field = 2
        # field to track 'select all' across paginated views = 1
        # 6 + 4 + 4 + 1 + 2 + 2 + 1 = 20 inputs
        self.assertContains(response, "<input", count=21)
        # 1 select per object = 3 selects
        self.assertContains(response, "<select", count=4)
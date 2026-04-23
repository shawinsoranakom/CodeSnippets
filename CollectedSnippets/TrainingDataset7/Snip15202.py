def test_list_display_ordering(self):
        from selenium.webdriver.common.by import By

        parent_a = Parent.objects.create(name="Parent A")
        child_l = Child.objects.create(name="Child L", parent=None)
        child_m = Child.objects.create(name="Child M", parent=parent_a)
        GrandChild.objects.create(name="Grandchild X", parent=child_m)
        GrandChild.objects.create(name="Grandchild Y", parent=child_l)
        GrandChild.objects.create(name="Grandchild Z", parent=None)

        self.admin_login(username="super", password="secret")
        changelist_url = reverse("admin:admin_changelist_grandchild_changelist")
        self.selenium.get(self.live_server_url + changelist_url)

        def find_result_row_texts():
            table = self.selenium.find_element(By.ID, "result_list")
            # Drop header from the result list
            return [row.text for row in table.find_elements(By.TAG_NAME, "tr")][1:]

        def expected_from_queryset(qs):
            return [
                " ".join("-" if i is None else i for i in item)
                for item in qs.values_list(
                    "name", "parent__name", "parent__parent__name"
                )
            ]

        cases = [
            # Order ascending by `name`.
            ("th.sortable.column-name", ("name",)),
            # Order descending by `name`.
            ("th.sortable.column-name", ("-name",)),
            # Order ascending by `parent__name`.
            ("th.sortable.column-parent__name", ("parent__name", "-name")),
            # Order descending by `parent__name`.
            ("th.sortable.column-parent__name", ("-parent__name", "-name")),
            # Order ascending by `parent__parent__name`.
            (
                "th.sortable.column-parent__parent__name",
                ("parent__parent__name", "-parent__name", "-name"),
            ),
            # Order descending by `parent__parent__name`.
            (
                "th.sortable.column-parent__parent__name",
                ("-parent__parent__name", "-parent__name", "-name"),
            ),
        ]
        for css_selector, ordering in cases:
            with self.subTest(ordering=ordering):
                self.selenium.find_element(By.CSS_SELECTOR, css_selector).click()
                expected = expected_from_queryset(
                    GrandChild.objects.all().order_by(*ordering)
                )
                self.assertEqual(find_result_row_texts(), expected)
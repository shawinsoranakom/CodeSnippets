def test_disallowed_to_field(self):
        url = reverse("admin:admin_views_section_changelist")
        with self.assertLogs("django.security.DisallowedModelAdminToField", "ERROR"):
            response = self.client.get(url, {TO_FIELD_VAR: "missing_field"})
        self.assertEqual(response.status_code, 400)

        # Specifying a field that is not referred by any other model registered
        # to this admin site should raise an exception.
        with self.assertLogs("django.security.DisallowedModelAdminToField", "ERROR"):
            response = self.client.get(
                reverse("admin:admin_views_section_changelist"), {TO_FIELD_VAR: "name"}
            )
        self.assertEqual(response.status_code, 400)

        # Primary key should always be allowed, even if the referenced model
        # isn't registered.
        response = self.client.get(
            reverse("admin:admin_views_notreferenced_changelist"), {TO_FIELD_VAR: "id"}
        )
        self.assertEqual(response.status_code, 200)

        # Specifying a field referenced by another model though a m2m should be
        # allowed.
        response = self.client.get(
            reverse("admin:admin_views_recipe_changelist"), {TO_FIELD_VAR: "rname"}
        )
        self.assertEqual(response.status_code, 200)

        # Specifying a field referenced through a reverse m2m relationship
        # should be allowed.
        response = self.client.get(
            reverse("admin:admin_views_ingredient_changelist"), {TO_FIELD_VAR: "iname"}
        )
        self.assertEqual(response.status_code, 200)

        # Specifying a field that is not referred by any other model directly
        # registered to this admin site but registered through inheritance
        # should be allowed.
        response = self.client.get(
            reverse("admin:admin_views_referencedbyparent_changelist"),
            {TO_FIELD_VAR: "name"},
        )
        self.assertEqual(response.status_code, 200)

        # Specifying a field that is only referred to by a inline of a
        # registered model should be allowed.
        response = self.client.get(
            reverse("admin:admin_views_referencedbyinline_changelist"),
            {TO_FIELD_VAR: "name"},
        )
        self.assertEqual(response.status_code, 200)

        # #25622 - Specifying a field of a model only referred by a generic
        # relation should raise DisallowedModelAdminToField.
        url = reverse("admin:admin_views_referencedbygenrel_changelist")
        with self.assertLogs("django.security.DisallowedModelAdminToField", "ERROR"):
            response = self.client.get(url, {TO_FIELD_VAR: "object_id"})
        self.assertEqual(response.status_code, 400)

        # We also want to prevent the add, change, and delete views from
        # leaking a disallowed field value.
        with self.assertLogs("django.security.DisallowedModelAdminToField", "ERROR"):
            response = self.client.post(
                reverse("admin:admin_views_section_add"), {TO_FIELD_VAR: "name"}
            )
        self.assertEqual(response.status_code, 400)

        section = Section.objects.create()
        url = reverse("admin:admin_views_section_change", args=(section.pk,))
        with self.assertLogs("django.security.DisallowedModelAdminToField", "ERROR"):
            response = self.client.post(url, {TO_FIELD_VAR: "name"})
        self.assertEqual(response.status_code, 400)

        url = reverse("admin:admin_views_section_delete", args=(section.pk,))
        with self.assertLogs("django.security.DisallowedModelAdminToField", "ERROR"):
            response = self.client.post(url, {TO_FIELD_VAR: "name"})
        self.assertEqual(response.status_code, 400)
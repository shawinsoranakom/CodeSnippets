def test_multiuser_edit(self):
        """
        Simultaneous edits of list_editable fields on the changelist by
        different users must not result in one user's edits creating a new
        object instead of modifying the correct existing object (#11313).
        """
        # To replicate this issue, simulate the following steps:
        # 1. User1 opens an admin changelist with list_editable fields.
        # 2. User2 edits object "Foo" such that it moves to another page in
        #    the pagination order and saves.
        # 3. User1 edits object "Foo" and saves.
        # 4. The edit made by User1 does not get applied to object "Foo" but
        #    instead is used to create a new object (bug).

        # For this test, order the changelist by the 'speed' attribute and
        # display 3 objects per page (SwallowAdmin.list_per_page = 3).

        # Setup the test to reflect the DB state after step 2 where User2 has
        # edited the first swallow object's speed from '4' to '1'.
        a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
        b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)
        c = Swallow.objects.create(origin="Swallow C", load=5, speed=5)
        d = Swallow.objects.create(origin="Swallow D", load=9, speed=9)

        superuser = self._create_superuser("superuser")
        self.client.force_login(superuser)
        changelist_url = reverse("admin:admin_changelist_swallow_changelist")

        # Send the POST from User1 for step 3. It's still using the changelist
        # ordering from before User2's edits in step 2.
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-uuid": str(d.pk),
            "form-1-uuid": str(c.pk),
            "form-2-uuid": str(a.pk),
            "form-0-load": "9.0",
            "form-0-speed": "9.0",
            "form-1-load": "5.0",
            "form-1-speed": "5.0",
            "form-2-load": "5.0",
            "form-2-speed": "4.0",
            "_save": "Save",
        }
        response = self.client.post(
            changelist_url, data, follow=True, extra={"o": "-2"}
        )

        # The object User1 edited in step 3 is displayed on the changelist and
        # has the correct edits applied.
        self.assertContains(response, "1 swallow was changed successfully.")
        self.assertContains(response, a.origin)
        a.refresh_from_db()
        self.assertEqual(a.load, float(data["form-2-load"]))
        self.assertEqual(a.speed, float(data["form-2-speed"]))
        b.refresh_from_db()
        self.assertEqual(b.load, 2)
        self.assertEqual(b.speed, 2)
        c.refresh_from_db()
        self.assertEqual(c.load, float(data["form-1-load"]))
        self.assertEqual(c.speed, float(data["form-1-speed"]))
        d.refresh_from_db()
        self.assertEqual(d.load, float(data["form-0-load"]))
        self.assertEqual(d.speed, float(data["form-0-speed"]))
        # No new swallows were created.
        self.assertEqual(len(Swallow.objects.all()), 4)
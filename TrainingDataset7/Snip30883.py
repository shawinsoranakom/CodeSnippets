def test_ticket_20955(self):
        jack = Staff.objects.create(name="jackstaff")
        jackstaff = StaffUser.objects.create(staff=jack)
        jill = Staff.objects.create(name="jillstaff")
        jillstaff = StaffUser.objects.create(staff=jill)
        task = Task.objects.create(creator=jackstaff, owner=jillstaff, title="task")
        task_get = Task.objects.get(pk=task.pk)
        # Load data so that assertNumQueries doesn't complain about the get
        # version's queries.
        task_get.creator.staffuser.staff
        task_get.owner.staffuser.staff
        qs = Task.objects.select_related(
            "creator__staffuser__staff", "owner__staffuser__staff"
        )
        self.assertEqual(str(qs.query).count(" JOIN "), 6)
        task_select_related = qs.get(pk=task.pk)
        with self.assertNumQueries(0):
            self.assertEqual(
                task_select_related.creator.staffuser.staff,
                task_get.creator.staffuser.staff,
            )
            self.assertEqual(
                task_select_related.owner.staffuser.staff,
                task_get.owner.staffuser.staff,
            )
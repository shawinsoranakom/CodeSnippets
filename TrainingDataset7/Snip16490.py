def test_actions_counter_is_live_region(self):
        response = self.client.get(reverse("admin:admin_views_person_changelist"))
        self.assertContains(
            response,
            (
                'class="action-counter" data-actions-icnt="3" '
                'aria-live="polite" aria-atomic="true"'
            ),
        )
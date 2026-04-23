def test_display_consecutive_whitespace_object_in_recent_action(self):
        for action in [ADDITION, DELETION]:
            LogEntry.objects.log_actions(
                user_id=self.user.pk,
                queryset=[self.obj],
                action_flag=action,
                change_message=[],
                single_object=True,
            )

        response = self.client.get(reverse("admin:index"))
        self.assertContains(
            response,
            '<li class="addlink"><span class="visually-hidden">Added:</span>'
            f'<a href="{self.change_link}">-</a><br><span class="mini quiet">'
            "Cover letter</span></li>",
            html=True,
        )
        self.assertContains(
            response,
            '<li class="deletelink">'
            '<span class="visually-hidden">Deleted:</span>-'
            '<br><span class="mini quiet">Cover letter</span></li>',
            html=True,
        )
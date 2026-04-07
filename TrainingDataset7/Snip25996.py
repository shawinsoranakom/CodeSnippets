def test_through_fields(self):
        """
        Relations with intermediary tables with multiple FKs
        to the M2M's ``to`` model are possible.
        """
        event = Event.objects.create(title="Rockwhale 2014")
        Invitation.objects.create(event=event, inviter=self.bob, invitee=self.jim)
        Invitation.objects.create(event=event, inviter=self.bob, invitee=self.jane)
        self.assertQuerySetEqual(
            event.invitees.all(), ["Jane", "Jim"], attrgetter("name")
        )
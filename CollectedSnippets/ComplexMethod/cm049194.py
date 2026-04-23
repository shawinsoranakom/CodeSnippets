def test_delete_one_event_and_future_from_recurrence_from_outlook_calendar(self, mock_get_events):
        if not self.sync_odoo_recurrences_with_outlook_feature():
            return
        # arrange
        idx = range(4, self.recurrent_events_count)
        rec_values = [
            dict(
                event,
                lastModifiedDateTime=_modified_date_in_the_future(self.recurrence)
            )
            for i, event in enumerate(self.recurrent_event_from_outlook_organizer)
            if i not in [x + 1 for x in idx]
        ]
        event_to_remove = [e for i, e in enumerate(self.recurrent_events) if i in idx]
        mock_get_events.return_value = (MicrosoftEvent(rec_values), None)

        # act
        self.organizer_user.with_user(self.organizer_user).sudo()._sync_microsoft_calendar()

        # assert
        for e in event_to_remove:
            self.assertFalse(e.exists())
        self.assertEqual(len(self.recurrence.calendar_event_ids), self.recurrent_events_count - len(idx))
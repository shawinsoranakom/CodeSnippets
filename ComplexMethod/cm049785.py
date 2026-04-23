def assertBusNotifications(self, channels, message_items=None, check_unique=True):
        """ Check bus notifications content. Mandatory and basic check is about
        channels being notified. Content check is optional.

        EXPECTED
        :param channels: list of expected bus channels, like [
          (self.cr.dbname, 'res.partner', self.partner_employee_2.id)
        ]
        :param message_items: if given, list of expected message making a valid
          pair (channel, message) to be found in bus.bus, like [
            {'type': 'mail.message/notification_update',
             'elements': {self.msg.id: {
                'message_id': self.msg.id,
                'message_type': 'sms',
                'notifications': {...},
                ...
              }}
            }, {...}]
        """
        self.env.cr.precommit.run()  # trigger the creation of bus.bus records
        bus_notifs = self.env['bus.bus'].sudo().search([('channel', 'in', [json_dump(channel) for channel in channels])])
        new_lines = "\n\n"

        def notif_to_string(notif):
            return f"{notif.channel}\n{notif.message}"

        self.assertEqual(
            bus_notifs.mapped("channel"),
            [json_dump(channel) for channel in channels],
            f"\n\nExpected:\n{new_lines[0].join([json_dump(channel) for channel in channels])}"
            f"\n\nReturned:\n{new_lines.join([notif_to_string(notif) for notif in bus_notifs])}",
        )
        for expected in message_items or []:
            for notification in bus_notifs:
                if json.loads(json_dump(expected)) == json.loads(notification.message):
                    break
            else:
                matching_notifs = [n for n in bus_notifs if json.loads(n.message).get("type") == expected.get("type")]
                if len(matching_notifs) == 1:
                    self.assertEqual(expected, json.loads(matching_notifs[0].message))
                if not matching_notifs:
                    matching_notifs = bus_notifs
                raise AssertionError(
                    "No notification was found with the expected value.\n\n"
                    f"Expected:\n{json_dump(expected)}\n\n"
                    f"Returned:\n{new_lines.join([notif_to_string(notif) for notif in matching_notifs])}"
                )
        if check_unique:
            self.assertEqual(len(bus_notifs), len(channels))
        return bus_notifs
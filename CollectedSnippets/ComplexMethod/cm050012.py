def adyen_webhook(self):
        """ Process the data sent by Adyen to the webhook based on the event code.

        See https://docs.adyen.com/development-resources/webhooks/understand-notifications for the
        exhaustive list of event codes.

        :return: The '[accepted]' string to acknowledge the notification
        :rtype: str
        """
        data = request.get_json_data()
        for notification_item in data['notificationItems']:
            payment_data = notification_item['NotificationRequestItem']

            _logger.info(
                "notification received from Adyen with data:\n%s", pprint.pformat(payment_data)
            )
            # Check the integrity of the notification.
            tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference(
                'adyen', payment_data
            )
            if tx_sudo:
                self._verify_signature(payment_data, tx_sudo)

                # Check whether the event of the notification succeeded and reshape the notification
                # data for parsing
                success = payment_data['success'] == 'true'
                event_code = payment_data['eventCode']
                if event_code == 'AUTHORISATION' and success:
                    payment_data['resultCode'] = 'Authorised'
                elif event_code == 'CANCELLATION':
                    payment_data['resultCode'] = 'Cancelled' if success else 'Error'
                elif event_code in ['REFUND', 'CAPTURE']:
                    payment_data['resultCode'] = 'Authorised' if success else 'Error'
                elif event_code == 'CAPTURE_FAILED' and success:
                    # The capture failed after a capture notification with success = True was sent
                    payment_data['resultCode'] = 'Error'
                else:
                    continue  # Don't handle unsupported event codes and failed events
                tx_sudo._process('adyen', payment_data)
        return request.make_json_response('[accepted]')
def _web_push_send_notification(self, devices, private_key, public_key, payload_by_lang=None, payload=None):
        """
        :param payload: JSON serializable dict following the notification api specs https://notifications.spec.whatwg.org/#api
        :param payload_by_lang a dict mapping payload by lang, either this or payload must be provided
        """
        if len(devices) < MAX_DIRECT_PUSH:
            session = Session()
            devices_to_unlink = set()
            for device in devices:
                try:
                    push_to_end_point(
                        base_url=self.get_base_url(),
                        device={
                            'id': device.id,
                            'endpoint': device.endpoint,
                            'keys': device.keys
                        },
                        payload=json.dumps(payload_by_lang and payload_by_lang[device.partner_id.lang] or payload),
                        vapid_private_key=private_key,
                        vapid_public_key=public_key,
                        session=session,
                    )
                except DeviceUnreachableError:
                    devices_to_unlink.add(device.id)
                except Exception as e:  # pylint: disable=broad-except
                    # Avoid blocking the whole request just for a notification
                    _logger.error('An error occurred while contacting the endpoint: %s', e)

            # clean up obsolete devices
            if devices_to_unlink:
                devices_list = list(devices_to_unlink)
                self.env['mail.push.device'].sudo().browse(devices_list).unlink()

        else:
            self.env['mail.push'].sudo().create([{
                'mail_push_device_id': device.id,
                'payload': json.dumps(payload_by_lang and payload_by_lang[device.partner_id.lang] or payload),
            } for device in devices])
            self.env.ref('mail.ir_cron_web_push_notification')._trigger()
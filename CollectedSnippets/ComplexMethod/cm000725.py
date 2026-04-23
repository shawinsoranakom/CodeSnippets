async def validate_payload(
        cls, webhook: Webhook, request, credentials: Credentials | None
    ) -> tuple[dict, str]:
        """Validate incoming webhook payload and signature."""

        if not credentials:
            raise ValueError("Missing credentials in webhook metadata")

        payload = await request.json()

        # Verify webhook signature using HMAC-SHA256
        if webhook.secret:
            mac_secret = webhook.config.get("mac_secret")
            if mac_secret:
                # Get the raw body for signature verification
                body = await request.body()

                # Calculate expected signature
                mac_secret_decoded = mac_secret.encode()
                hmac_obj = hmac.new(mac_secret_decoded, body, hashlib.sha256)
                expected_mac = f"hmac-sha256={hmac_obj.hexdigest()}"

                # Get signature from headers
                signature = request.headers.get("X-Airtable-Content-MAC")

                if signature and not hmac.compare_digest(signature, expected_mac):
                    raise ValueError("Invalid webhook signature")

        # Validate payload structure
        required_fields = ["base", "webhook", "timestamp"]
        if not all(field in payload for field in required_fields):
            raise ValueError("Invalid webhook payload structure")

        if "id" not in payload["base"] or "id" not in payload["webhook"]:
            raise ValueError("Missing required IDs in webhook payload")
        base_id = payload["base"]["id"]
        webhook_id = payload["webhook"]["id"]

        # get payload request parameters
        cursor = webhook.config.get("cursor", 1)

        response = await list_webhook_payloads(credentials, base_id, webhook_id, cursor)

        # update webhook config
        await update_webhook(
            webhook.id,
            config=cast(
                dict[str, Serializable], {"base_id": base_id, "cursor": response.cursor}
            ),
        )

        event_type = "notification"
        return response.model_dump(), event_type
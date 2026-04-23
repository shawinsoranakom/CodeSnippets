async def validate_payload(
        cls,
        webhook: integrations.Webhook,
        request: Request,
        credentials: Credentials | None,
    ) -> tuple[dict, str]:
        """
        Validates incoming Telegram webhook request.

        Telegram sends X-Telegram-Bot-Api-Secret-Token header when secret_token
        was set in setWebhook call.

        Returns:
            tuple: (payload dict, event_type string)
        """
        # Verify secret token header
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not secret_header or not hmac.compare_digest(secret_header, webhook.secret):
            raise HTTPException(
                status_code=403,
                detail="Invalid or missing X-Telegram-Bot-Api-Secret-Token",
            )

        payload = await request.json()

        # Determine event type based on update content
        if "message" in payload:
            message = payload["message"]
            if "text" in message:
                event_type = "message.text"
            elif "photo" in message:
                event_type = "message.photo"
            elif "voice" in message:
                event_type = "message.voice"
            elif "audio" in message:
                event_type = "message.audio"
            elif "document" in message:
                event_type = "message.document"
            elif "video" in message:
                event_type = "message.video"
            else:
                event_type = "message.other"
        elif "edited_message" in payload:
            event_type = "message.edited_message"
        elif "message_reaction" in payload:
            event_type = "message_reaction"
        else:
            event_type = "unknown"

        return payload, event_type
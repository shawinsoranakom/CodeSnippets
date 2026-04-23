async def _forward_message(
        self, service, input_data: Input, execution_context: ExecutionContext
    ) -> dict:
        if not input_data.to:
            raise ValueError("At least one recipient is required for forwarding")

        # Get the original message
        original = await asyncio.to_thread(
            lambda: service.users()
            .messages()
            .get(userId="me", id=input_data.messageId, format="full")
            .execute()
        )

        headers = {
            h["name"].lower(): h["value"]
            for h in original.get("payload", {}).get("headers", [])
        }

        # Create subject with Fwd: prefix if not already present
        original_subject = headers.get("subject", "No Subject")
        if input_data.subject:
            subject = input_data.subject
        elif not original_subject.lower().startswith("fwd:"):
            subject = f"Fwd: {original_subject}"
        else:
            subject = original_subject

        # Build forwarded message body
        original_from = headers.get("from", "Unknown")
        original_date = headers.get("date", "Unknown")
        original_to = headers.get("to", "Unknown")

        # Get the original body
        original_body = await self._get_email_body(original, service)

        # Construct the forward header
        forward_header = f"""
---------- Forwarded message ---------
From: {original_from}
Date: {original_date}
Subject: {original_subject}
To: {original_to}
"""

        # Combine optional forward message with original content
        if input_data.forwardMessage:
            body = f"{input_data.forwardMessage}\n\n{forward_header}\n\n{original_body}"
        else:
            body = f"{forward_header}\n\n{original_body}"

        # Validate all recipient lists before building the MIME message
        validate_all_recipients(input_data)

        # Create MIME message
        msg = MIMEMultipart()
        msg["To"] = serialize_email_recipients(input_data.to)
        if input_data.cc:
            msg["Cc"] = serialize_email_recipients(input_data.cc)
        if input_data.bcc:
            msg["Bcc"] = serialize_email_recipients(input_data.bcc)
        msg["Subject"] = subject

        # Add body with proper content type
        msg.attach(_make_mime_text(body, input_data.content_type))

        # Include original attachments if requested
        if input_data.includeAttachments:
            attachments = await self._get_attachments(service, original)
            for attachment in attachments:
                # Download and attach each original attachment
                attachment_data = await self.download_attachment(
                    service, input_data.messageId, attachment.attachment_id
                )
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_data)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment.filename}",
                )
                msg.attach(part)

        # Add any additional attachments
        for attach in input_data.additionalAttachments:
            local_path = await store_media_file(
                file=attach,
                execution_context=execution_context,
                return_format="for_local_processing",
            )
            assert execution_context.graph_exec_id  # Validated by store_media_file
            abs_path = get_exec_file_path(execution_context.graph_exec_id, local_path)
            part = MIMEBase("application", "octet-stream")
            with open(abs_path, "rb") as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename={Path(abs_path).name}"
            )
            msg.attach(part)

        # Send the forwarded message
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        return await asyncio.to_thread(
            lambda: service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
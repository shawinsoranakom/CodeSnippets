def send_email(
        self,
        context: RequestContext,
        source: Address,
        destination: Destination,
        message: Message,
        reply_to_addresses: AddressList = None,
        return_path: Address = None,
        source_arn: AmazonResourceName = None,
        return_path_arn: AmazonResourceName = None,
        tags: MessageTagList = None,
        configuration_set_name: ConfigurationSetName = None,
        **kwargs,
    ) -> SendEmailResponse:
        if tags:
            for tag in tags:
                tag_name = tag.get("Name", "")
                tag_value = tag.get("Value", "")
                if tag_name == "":
                    raise InvalidParameterValue("The tag name must be specified.")
                if tag_value == "":
                    raise InvalidParameterValue("The tag value must be specified.")
                if len(tag_name) > 255:
                    raise InvalidParameterValue("Tag name cannot exceed 255 characters.")
                # The `ses:` prefix is for a special case and disregarded for validation
                # see https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing.html#event-publishing-fine-grained-feedback
                if not re.match(REGEX_TAG_NAME, tag_name.removeprefix("ses:")):
                    raise InvalidParameterValue(
                        f"Invalid tag name <{tag_name}>: only alphanumeric ASCII characters, '_',  '-' are allowed.",
                    )
                if len(tag_value) > 255:
                    raise InvalidParameterValue("Tag value cannot exceed 255 characters.")
                if not re.match(REGEX_TAG_VALUE, tag_value):
                    raise InvalidParameterValue(
                        f"Invalid tag value <{tag_value}>: only alphanumeric ASCII characters, '_',  '-' , '.', '@' are allowed.",
                    )

        response = call_moto(context)

        backend = get_ses_backend(context)

        if event_destinations := backend.config_set_event_destination.get(configuration_set_name):
            recipients = recipients_from_destination(destination)
            payload = EventDestinationPayload(
                message_id=response["MessageId"],
                sender_email=source,
                destination_addresses=recipients,
                tags=tags,
            )
            notify_event_destinations(
                context=context,
                event_destinations=event_destinations,
                payload=payload,
                email_type=EmailType.EMAIL,
            )

        text_part = message["Body"].get("Text", {}).get("Data")
        html_part = message["Body"].get("Html", {}).get("Data")

        save_for_retrospection(
            SentEmail(
                Id=response["MessageId"],
                Region=context.region,
                Destination=destination,
                Source=source,
                Subject=message["Subject"].get("Data"),
                Body=SentEmailBody(text_part=text_part, html_part=html_part),
            )
        )

        return response
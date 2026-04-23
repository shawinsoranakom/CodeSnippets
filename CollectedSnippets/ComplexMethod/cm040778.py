def _publish(self, context: SnsBatchPublishContext, subscriber: SnsSubscription):
        entries = []
        sqs_system_attrs = create_sqs_system_attributes(context.request_headers)
        # TODO: check ID, SNS rules are not the same as SQS, so maybe generate the entries ID
        failure_map = {}
        for index, message_ctx in enumerate(context.messages):
            message_body = self.prepare_message(
                message_ctx, subscriber, topic_attributes=context.topic_attributes
            )
            sqs_kwargs = self.get_sqs_kwargs(message_ctx, subscriber)
            entry = {"Id": f"sns-batch-{index}", "MessageBody": message_body, **sqs_kwargs}
            # in case of failure
            failure_map[entry["Id"]] = {
                "context": message_ctx,
                "entry": entry,
            }

            if sqs_system_attrs:
                entry["MessageSystemAttributes"] = sqs_system_attrs

            entries.append(entry)

        try:
            queue_url = sqs_queue_url_for_arn(subscriber["Endpoint"])

            account_id = extract_account_id_from_arn(subscriber["Endpoint"])
            region = extract_region_from_arn(subscriber["Endpoint"])

            sqs_client = connect_to(
                aws_access_key_id=account_id, region_name=region
            ).sqs.request_metadata(source_arn=subscriber["TopicArn"], service_principal="sns")
            response = sqs_client.send_message_batch(QueueUrl=queue_url, Entries=entries)

            for message_ctx in context.messages:
                store_delivery_log(
                    message_ctx, subscriber, success=True, topic_attributes=context.topic_attributes
                )

            if failed_messages := response.get("Failed"):
                for failed_msg in failed_messages:
                    failure_data = failure_map.get(failed_msg["Id"])
                    LOG.info(
                        "Unable to forward SNS message to SQS: %s %s",
                        failed_msg["Code"],
                        failed_msg["Message"],
                    )
                    store_delivery_log(
                        failure_data["context"],
                        subscriber,
                        success=False,
                        topic_attributes=context.topic_attributes,
                    )
                    kwargs = {}
                    if msg_attrs := failure_data["entry"].get("MessageAttributes"):
                        kwargs["MessageAttributes"] = msg_attrs

                    if msg_group_id := failure_data["context"].get("MessageGroupId"):
                        kwargs["MessageGroupId"] = msg_group_id

                    if msg_dedup_id := failure_data["context"].get("MessageDeduplicationId"):
                        kwargs["MessageDeduplicationId"] = msg_dedup_id

                    sns_error_to_dead_letter_queue(
                        sns_subscriber=subscriber,
                        message=failure_data["entry"]["MessageBody"],
                        error=failed_msg["Code"],
                        **kwargs,
                    )

        except Exception as exc:
            LOG.info("Unable to forward SNS message to SQS: %s %s", exc, traceback.format_exc())
            for message_ctx in context.messages:
                store_delivery_log(
                    message_ctx,
                    subscriber,
                    success=False,
                    topic_attributes=context.topic_attributes,
                )
                msg_body = self.prepare_message(
                    message_ctx, subscriber, topic_attributes=context.topic_attributes
                )
                kwargs = self.get_sqs_kwargs(message_ctx, subscriber)

                sns_error_to_dead_letter_queue(
                    subscriber,
                    msg_body,
                    str(exc),
                    **kwargs,
                )
            if "NonExistentQueue" in str(exc):
                LOG.debug("The SQS queue endpoint does not exist anymore")
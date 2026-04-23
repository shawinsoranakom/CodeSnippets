async def _process_existing_batches(
        self, notification_types: list[NotificationType]
    ):
        """Process existing batches for specified notification types"""
        try:
            processed_count = 0
            current_time = datetime.now(tz=timezone.utc)

            for notification_type in notification_types:
                # Get all batches for this notification type
                batches = await get_database_manager_async_client(
                    should_retry=False
                ).get_all_batches_by_type(notification_type)

                for batch in batches:
                    # Check if batch has aged out
                    oldest_message = await get_database_manager_async_client(
                        should_retry=False
                    ).get_user_notification_oldest_message_in_batch(
                        batch.user_id, notification_type
                    )

                    if not oldest_message:
                        logger.warning(
                            f"Batch for user {batch.user_id} and type {notification_type} "
                            f"has no oldest message — batch may have been cleared concurrently"
                        )
                        continue

                    max_delay = get_batch_delay(notification_type)

                    # If batch has aged out, process it
                    if oldest_message.created_at + max_delay < current_time:
                        recipient_email = await get_database_manager_async_client(
                            should_retry=False
                        ).get_user_email_by_id(batch.user_id)

                        if not recipient_email:
                            logger.warning(
                                f"User email not found for user {batch.user_id}"
                            )
                            continue

                        should_send = await self._should_email_user_based_on_preference(
                            batch.user_id, notification_type
                        )

                        if not should_send:
                            logger.debug(
                                f"User {batch.user_id} does not want to receive {notification_type} notifications"
                            )
                            # Clear the batch
                            await get_database_manager_async_client(
                                should_retry=False
                            ).empty_user_notification_batch(
                                batch.user_id, notification_type
                            )
                            continue

                        batch_data = await get_database_manager_async_client(
                            should_retry=False
                        ).get_user_notification_batch(batch.user_id, notification_type)

                        if not batch_data or not batch_data.notifications:
                            logger.warning(
                                f"Batch data not found for user {batch.user_id}"
                            )
                            # Clear the batch
                            await get_database_manager_async_client(
                                should_retry=False
                            ).empty_user_notification_batch(
                                batch.user_id, notification_type
                            )
                            continue

                        unsub_link = generate_unsubscribe_link(batch.user_id)
                        events = []
                        for db_event in batch_data.notifications:
                            try:
                                events.append(
                                    NotificationEventModel[
                                        get_notif_data_type(db_event.type)
                                    ].model_validate(
                                        {
                                            "user_id": batch.user_id,
                                            "type": db_event.type,
                                            "data": db_event.data,
                                            "created_at": db_event.created_at,
                                        }
                                    )
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Error parsing notification event: {e=}, {db_event=}"
                                )
                                continue
                        logger.info(f"{events=}")

                        await self.email_sender.send_templated(
                            notification=notification_type,
                            user_email=recipient_email,
                            data=events,
                            user_unsub_link=unsub_link,
                        )

                        # Clear the batch
                        await get_database_manager_async_client(
                            should_retry=False
                        ).empty_user_notification_batch(
                            batch.user_id, notification_type
                        )

                        processed_count += 1

            logger.info(f"Processed {processed_count} aged batches")
            return {
                "success": True,
                "processed_count": processed_count,
                "notification_types": [nt.value for nt in notification_types],
                "timestamp": current_time.isoformat(),
            }

        except Exception as e:
            logger.exception(f"Error processing batches: {e}")
            return {
                "success": False,
                "error": str(e),
                "notification_types": [nt.value for nt in notification_types],
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
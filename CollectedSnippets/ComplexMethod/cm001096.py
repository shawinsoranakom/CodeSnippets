async def _process_batch(self, message: str) -> bool:
        """Process a single notification with a batching strategy, returning whether to put into the failed queue"""
        try:
            event = self._parse_message(message)
            if not event:
                return False
            logger.info(f"Processing batch notification: {event}")

            recipient_email = await get_database_manager_async_client(
                should_retry=False
            ).get_user_email_by_id(event.user_id)
            if not recipient_email:
                logger.warning(f"User email not found for user {event.user_id}")
                return False

            should_send = await self._should_email_user_based_on_preference(
                event.user_id, event.type
            )
            if not should_send:
                logger.info(
                    f"User {event.user_id} does not want to receive {event.type} notifications"
                )
                return True

            should_send = await self._should_batch(event.user_id, event.type, event)

            if not should_send:
                logger.info("Batch not old enough to send")
                return False
            batch = await get_database_manager_async_client(
                should_retry=False
            ).get_user_notification_batch(event.user_id, event.type)
            if not batch or not batch.notifications:
                logger.warning(f"Batch not found for user {event.user_id}")
                return False
            unsub_link = generate_unsubscribe_link(event.user_id)

            batch_messages = [
                NotificationEventModel[
                    get_notif_data_type(db_event.type)
                ].model_validate(
                    {
                        "id": db_event.id,  # Include ID from database
                        "user_id": event.user_id,
                        "type": db_event.type,
                        "data": db_event.data,
                        "created_at": db_event.created_at,
                    }
                )
                for db_event in batch.notifications
            ]

            # Split batch into chunks to avoid exceeding email size limits
            # Start with a reasonable chunk size and adjust dynamically
            MAX_EMAIL_SIZE = 4_500_000  # 4.5MB to leave buffer under 5MB limit
            chunk_size = 100  # Initial chunk size
            successfully_sent_count = 0
            failed_indices = []

            i = 0
            while i < len(batch_messages):
                # Try progressively smaller chunks if needed
                chunk_sent = False
                for attempt_size in [chunk_size, 50, 25, 10, 5, 1]:
                    chunk = batch_messages[i : i + attempt_size]
                    chunk_ids = [
                        msg.id for msg in chunk if msg.id
                    ]  # Extract IDs for removal

                    try:
                        # Try to render the email to check its size
                        template = self.email_sender._get_template(event.type)
                        _, test_message = (
                            await self.email_sender.formatter.format_email(
                                base_template=template.base_template,
                                subject_template=template.subject_template,
                                content_template=template.body_template,
                                data={"notifications": chunk},
                                unsubscribe_link=f"{self.email_sender.formatter.env.globals.get('base_url', '')}/profile/settings",
                            )
                        )

                        if len(test_message) < MAX_EMAIL_SIZE:
                            # Size is acceptable, send the email
                            logger.info(
                                f"Sending email with {len(chunk)} notifications "
                                f"(size: {len(test_message):,} chars)"
                            )

                            await self.email_sender.send_templated(
                                notification=event.type,
                                user_email=recipient_email,
                                data=chunk,
                                user_unsub_link=unsub_link,
                            )

                            # Remove successfully sent notifications immediately
                            if chunk_ids:
                                try:
                                    await get_database_manager_async_client(
                                        should_retry=False
                                    ).remove_notifications_from_batch(
                                        event.user_id, event.type, chunk_ids
                                    )
                                    logger.info(
                                        f"Removed {len(chunk_ids)} sent notifications from batch"
                                    )
                                except Exception as e:
                                    logger.warning(
                                        f"Failed to remove sent notifications: {e}"
                                    )
                                    # Continue anyway - better to risk duplicates than lose emails

                            # Track successful sends
                            successfully_sent_count += len(chunk)

                            # Update chunk_size for next iteration based on success
                            if (
                                attempt_size == chunk_size
                                and len(test_message) < MAX_EMAIL_SIZE * 0.7
                            ):
                                # If we're well under limit, try larger chunks next time
                                chunk_size = min(chunk_size + 10, 100)
                            elif len(test_message) > MAX_EMAIL_SIZE * 0.9:
                                # If we're close to limit, use smaller chunks
                                chunk_size = max(attempt_size - 10, 1)

                            i += len(chunk)
                            chunk_sent = True
                            break
                        else:
                            # Message is too large even after size reduction
                            if attempt_size == 1:
                                logger.warning(
                                    f"Failed to send notification at index {i}: "
                                    f"Single notification exceeds email size limit "
                                    f"({len(test_message):,} chars > {MAX_EMAIL_SIZE:,} chars). "
                                    f"Removing permanently from batch - will not retry."
                                )

                                # Remove the oversized notification permanently - it will NEVER fit
                                if chunk_ids:
                                    try:
                                        await get_database_manager_async_client(
                                            should_retry=False
                                        ).remove_notifications_from_batch(
                                            event.user_id, event.type, chunk_ids
                                        )
                                        logger.info(
                                            f"Removed oversized notification {chunk_ids[0]} from batch permanently"
                                        )
                                    except Exception as e:
                                        logger.warning(
                                            f"Failed to remove oversized notification: {e}"
                                        )

                                failed_indices.append(i)
                                i += 1
                                chunk_sent = True
                                break
                            # Try smaller chunk size
                            continue
                    except Exception as e:
                        # Check if it's a Postmark API error
                        if attempt_size == 1:
                            # Single notification failed - determine the actual cause
                            error_message = str(e).lower()
                            error_type = type(e).__name__

                            # Check for HTTP 406 - Inactive recipient (common in Postmark errors)
                            if "406" in error_message or "inactive" in error_message:
                                logger.warning(
                                    f"Failed to send notification at index {i}: "
                                    f"Recipient marked as inactive by Postmark. "
                                    f"Error: {e}. Disabling ALL notifications for this user."
                                )

                                # 1. Mark email as unverified
                                try:
                                    await set_user_email_verification(
                                        event.user_id, False
                                    )
                                    logger.info(
                                        f"Set email verification to false for user {event.user_id}"
                                    )
                                except Exception as deactivation_error:
                                    logger.warning(
                                        f"Failed to deactivate email for user {event.user_id}: "
                                        f"{deactivation_error}"
                                    )

                                # 2. Disable all notification preferences
                                try:
                                    await disable_all_user_notifications(event.user_id)
                                    logger.info(
                                        f"Disabled all notification preferences for user {event.user_id}"
                                    )
                                except Exception as disable_error:
                                    logger.warning(
                                        f"Failed to disable notification preferences: {disable_error}"
                                    )

                                # 3. Clear ALL notification batches for this user
                                try:
                                    await get_database_manager_async_client(
                                        should_retry=False
                                    ).clear_all_user_notification_batches(event.user_id)
                                    logger.info(
                                        f"Cleared ALL notification batches for user {event.user_id}"
                                    )
                                except Exception as remove_error:
                                    logger.warning(
                                        f"Failed to clear batches for inactive recipient: {remove_error}"
                                    )

                                # Stop processing - we've nuked everything for this user
                                return True
                            # Check for HTTP 422 - Malformed data
                            elif (
                                "422" in error_message
                                or "unprocessable" in error_message
                            ):
                                logger.warning(
                                    f"Failed to send notification at index {i}: "
                                    f"Malformed notification data rejected by Postmark. "
                                    f"Error: {e}. Removing from batch permanently."
                                )

                                # Remove from batch - 422 means bad data that won't fix itself
                                if chunk_ids:
                                    try:
                                        await get_database_manager_async_client(
                                            should_retry=False
                                        ).remove_notifications_from_batch(
                                            event.user_id, event.type, chunk_ids
                                        )
                                        logger.info(
                                            "Removed malformed notification from batch permanently"
                                        )
                                    except Exception as remove_error:
                                        logger.warning(
                                            f"Failed to remove malformed notification: {remove_error}"
                                        )
                            # Check if it's a ValueError for size limit
                            elif (
                                isinstance(e, ValueError)
                                and "too large" in error_message
                            ):
                                logger.warning(
                                    f"Failed to send notification at index {i}: "
                                    f"Notification size exceeds email limit. "
                                    f"Error: {e}. Skipping this notification."
                                )
                            # Other API errors
                            else:
                                logger.warning(
                                    f"Failed to send notification at index {i}: "
                                    f"Email API error ({error_type}): {e}. "
                                    f"Skipping this notification."
                                )

                            failed_indices.append(i)
                            i += 1
                            chunk_sent = True
                            break
                        # Try smaller chunk
                        continue

                if not chunk_sent:
                    # Should not reach here due to single notification handling
                    logger.warning(
                        f"Failed to send notifications starting at index {i}"
                    )
                    failed_indices.append(i)
                    i += 1

            # Check what remains in the batch (notifications are removed as sent)
            remaining_batch = await get_database_manager_async_client(
                should_retry=False
            ).get_user_notification_batch(event.user_id, event.type)

            if not remaining_batch or not remaining_batch.notifications:
                logger.info(
                    f"All {successfully_sent_count} notifications sent and removed from batch"
                )
            else:
                remaining_count = len(remaining_batch.notifications)
                logger.warning(
                    f"Sent {successfully_sent_count} notifications. "
                    f"{remaining_count} remain in batch for retry due to errors."
                )
            return True
        except Exception as e:
            logger.exception(f"Error processing notification for batch queue: {e}")
            return False
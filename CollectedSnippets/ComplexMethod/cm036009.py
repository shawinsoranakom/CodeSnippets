def sync_users_to_resend():
    """Sync users from Keycloak to Resend.

    This function syncs users from Keycloak to a Resend audience. It tracks
    which users have been synced in the database to ensure that:
    1. Users are only added once (even across multiple sync runs)
    2. Users who are manually deleted from Resend are not re-added

    The tracking is done via the resend_synced_users table, which records
    each email/audience_id combination that has been synced.

    On first run (or when new contacts exist in Resend), it will backfill
    the tracking table with existing Resend contacts to avoid sending
    duplicate welcome emails.
    """
    # Check required environment variables
    required_vars = {
        'RESEND_API_KEY': RESEND_API_KEY,
        'RESEND_AUDIENCE_ID': RESEND_AUDIENCE_ID,
        'KEYCLOAK_SERVER_URL': KEYCLOAK_SERVER_URL,
        'KEYCLOAK_REALM_NAME': KEYCLOAK_REALM_NAME,
        'KEYCLOAK_ADMIN_PASSWORD': KEYCLOAK_ADMIN_PASSWORD,
    }

    missing_vars = [var for var, value in required_vars.items() if not value]

    if missing_vars:
        for var in missing_vars:
            logger.error(f'{var} environment variable is not set')
        sys.exit(1)

    # Log configuration (without sensitive info)
    logger.info(f'Using Keycloak server: {KEYCLOAK_SERVER_URL}')
    logger.info(f'Using Keycloak realm: {KEYCLOAK_REALM_NAME}')

    logger.info(
        f'Starting sync of Keycloak users to Resend audience {RESEND_AUDIENCE_ID}'
    )

    try:
        # Get the store for tracking synced users
        synced_user_store = _get_resend_synced_user_store()

        # Backfill existing Resend contacts into our tracking table
        # This ensures users already in Resend don't get duplicate welcome emails
        backfilled_count = _backfill_existing_resend_contacts(
            synced_user_store, RESEND_AUDIENCE_ID
        )

        # Get the total number of users
        total_users = get_total_keycloak_users()
        logger.info(
            f'Found {total_users} users in Keycloak realm {KEYCLOAK_REALM_NAME}'
        )

        # Stats
        stats = {
            'total_users': total_users,
            'backfilled_contacts': backfilled_count,
            'already_synced': 0,
            'added_contacts': 0,
            'skipped_invalid_emails': 0,
            'errors': 0,
        }

        synced_emails = synced_user_store.get_synced_emails_for_audience(
            RESEND_AUDIENCE_ID
        )
        logger.info(f'Found {len(synced_emails)} already synced emails in database')

        # Process users in batches
        offset = 0
        while offset < total_users:
            users = get_keycloak_users(offset, BATCH_SIZE)
            logger.info(f'Processing batch of {len(users)} users (offset {offset})')

            for user in users:
                email = user.get('email')
                if not email:
                    continue

                email = email.lower()

                if email in synced_emails:
                    logger.debug(
                        f'User {email} was already synced to this audience, skipping'
                    )
                    stats['already_synced'] += 1
                    continue

                # Validate email format before attempting to add to Resend
                if not is_valid_email(email):
                    logger.warning(f'Skipping user with invalid email format: {email}')
                    stats['skipped_invalid_emails'] += 1
                    continue

                first_name = user.get('first_name')
                last_name = user.get('last_name')
                keycloak_user_id = user.get('id')

                # Mark as synced first (optimistic) to ensure consistency.
                # If Resend API fails, we remove the record.
                try:
                    synced_user_store.mark_user_synced(
                        email=email,
                        audience_id=RESEND_AUDIENCE_ID,
                        keycloak_user_id=keycloak_user_id,
                    )
                except Exception:
                    logger.exception(f'Failed to mark user {email} as synced')
                    stats['errors'] += 1
                    continue

                try:
                    add_contact_to_resend(
                        RESEND_AUDIENCE_ID, email, first_name, last_name
                    )
                    logger.info(f'Added user {email} to Resend')
                except Exception:
                    logger.exception(f'Error adding user {email} to Resend')
                    synced_user_store.remove_synced_user(email, RESEND_AUDIENCE_ID)
                    stats['errors'] += 1
                    continue

                synced_emails.add(email)
                stats['added_contacts'] += 1

                # Sleep to respect rate limit after first API call
                time.sleep(1 / RATE_LIMIT)

                # Send a welcome email to the newly added contact
                try:
                    send_welcome_email(email, first_name, last_name)
                    logger.info(f'Sent welcome email to {email}')
                except Exception:
                    logger.exception(
                        f'Failed to send welcome email to {email}, but contact was added to audience'
                    )

                # Sleep to respect rate limit after second API call
                time.sleep(1 / RATE_LIMIT)

            offset += BATCH_SIZE

        logger.info(f'Sync completed: {stats}')
    except KeycloakClientError:
        logger.exception('Keycloak client error')
        sys.exit(1)
    except ResendAPIError:
        logger.exception('Resend API error')
        sys.exit(1)
    except Exception:
        logger.exception('Sync failed with unexpected error')
        sys.exit(1)
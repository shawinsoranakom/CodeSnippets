async def downgrade_user(user_id: str) -> UserSettings | None:
        """This method can be removed once orgs is established - probably after Feb 15 2026
        Downgrade a migrated user back to the pre-migration state.

        This reverses the migrate_user operation:
        1. Get the user's settings from user_settings table (migrated users) or
           create new user_settings from org_members table (new sign-ups)
        2. Call LiteLlmManager.downgrade_entries to revert LiteLLM state
        3. Copy user_id from conversation_metadata_saas to conversation_metadata
        4. Delete conversation_metadata_saas entries
        5. Reset org_id columns in related tables (stripe_customers, slack_users, etc.)
        6. Delete the org_member and org entries
        7. Delete the user entry
        8. Set already_migrated=False on user_settings

        For new sign-ups (users who registered after migration was deployed),
        there won't be an existing user_settings entry. In this case, we fall back
        to the org_members table to get the user's API keys and settings, and create
        a new user_settings entry for them.

        Args:
            user_id: The Keycloak user ID to downgrade

        Returns:
            The user_settings if downgrade was successful, None otherwise.
            Returns None if the org has multiple members (not a personal org).
        """
        logger.info(
            'user_store:downgrade_user:start',
            extra={'user_id': user_id},
        )

        async with a_session_maker() as session:
            # Get the user and their org_member
            result = await session.execute(
                select(User)
                .options(selectinload(User.org_members))
                .filter(User.id == uuid.UUID(user_id))
            )
            user = result.scalars().first()
            if not user:
                logger.warning(
                    'user_store:downgrade_user:user_not_found',
                    extra={'user_id': user_id},
                )
                return None

            # Get the user's personal org (org_id == user_id)
            result = await session.execute(
                select(Org).filter(Org.id == uuid.UUID(user_id))
            )
            org = result.scalars().first()
            if not org:
                logger.warning(
                    'user_store:downgrade_user:org_not_found',
                    extra={'user_id': user_id},
                )
                return None

            # Get org_members for this org - should only be one for personal orgs
            result = await session.execute(
                select(OrgMember).filter(OrgMember.org_id == org.id)
            )
            org_members = result.scalars().all()

            if len(org_members) != 1:
                logger.error(
                    'user_store:downgrade_user:unexpected_org_members_count',
                    extra={
                        'user_id': user_id,
                        'org_id': str(org.id),
                        'org_members_count': len(org_members),
                    },
                )
                return None

            org_member = org_members[0]

            # Get the user_settings (for migrated users)
            result = await session.execute(
                select(UserSettings).filter(
                    UserSettings.keycloak_user_id == user_id,
                    UserSettings.already_migrated.is_(True),
                )
            )
            user_settings = result.scalars().first()

            # For new sign-ups after migration, user_settings won't exist
            # Fall back to getting data from org_members
            if user_settings:
                if org_member.llm_api_key and org_member.llm_api_key.get_secret_value():
                    user_settings.llm_api_key = encrypt_legacy_value(
                        org_member.llm_api_key.get_secret_value()
                    )
                if (
                    org_member.llm_api_key_for_byor
                    and org_member.llm_api_key_for_byor.get_secret_value()
                ):
                    user_settings.llm_api_key_for_byor = encrypt_legacy_value(
                        org_member.llm_api_key_for_byor.get_secret_value()
                    )
                logger.info(
                    'user_store:downgrade_user:updated_user_settings_from_org_member',
                    extra={'user_id': user_id},
                )
            else:
                # Create a new user_settings entry from OrgMember, User, and Org data
                # This is needed for new sign-ups who don't have user_settings
                user_settings = UserStore._create_user_settings_from_entities(
                    user_id, org_member, user, org
                )
                session.add(user_settings)
                logger.info(
                    'user_store:downgrade_user:created_user_settings_from_org_member',
                    extra={'user_id': user_id},
                )
            await session.flush()

            # Call LiteLLM downgrade
            from storage.lite_llm_manager import LiteLlmManager

            logger.debug(
                'user_store:downgrade_user:calling_litellm_downgrade_entries',
                extra={'user_id': user_id},
            )

            encrypted_fields = [
                'llm_api_key',
                'llm_api_key_for_byor',
                'search_api_key',
                'sandbox_api_key',
            ]
            for field in encrypted_fields:
                value = getattr(user_settings, field, None)
                if value:
                    try:
                        value = decrypt_legacy_value(value)
                        setattr(user_settings, field, value)
                    except Exception:
                        pass

            await LiteLlmManager.downgrade_entries(
                str(org.id),
                user_id,
                user_settings,
            )
            logger.debug(
                'user_store:downgrade_user:done_litellm_downgrade_entries',
                extra={'user_id': user_id},
            )

            user_uuid = uuid.UUID(user_id)

            # Step 3: Copy user_id from conversation_metadata_saas to conversation_metadata
            # This ensures any conversations created after migration have their user_id
            # preserved in the original table before we delete the saas entries
            await session.execute(
                text("""
                    UPDATE conversation_metadata
                    SET user_id = :user_id
                    WHERE conversation_id IN (
                        SELECT conversation_id
                        FROM conversation_metadata_saas
                        WHERE user_id = :user_uuid
                    )
                """),
                {'user_id': user_id, 'user_uuid': user_uuid},
            )

            # Step 4: Delete conversation_metadata_saas entries
            await session.execute(
                text('DELETE FROM conversation_metadata_saas WHERE user_id = :user_id'),
                {'user_id': user_uuid},
            )

            # Step 5: Reset org_id columns in related tables
            # Reset stripe_customers
            await session.execute(
                text(
                    'UPDATE stripe_customers SET org_id = NULL WHERE org_id = :org_id'
                ),
                {'org_id': user_uuid},
            )

            # Reset slack_users
            await session.execute(
                text('UPDATE slack_users SET org_id = NULL WHERE org_id = :org_id'),
                {'org_id': user_uuid},
            )

            # Reset slack_conversation
            await session.execute(
                text(
                    'UPDATE slack_conversation SET org_id = NULL WHERE org_id = :org_id'
                ),
                {'org_id': user_uuid},
            )

            # Reset api_keys
            await session.execute(
                text('UPDATE api_keys SET org_id = NULL WHERE org_id = :org_id'),
                {'org_id': user_uuid},
            )

            # Reset custom_secrets
            await session.execute(
                text('UPDATE custom_secrets SET org_id = NULL WHERE org_id = :org_id'),
                {'org_id': user_uuid},
            )

            # Reset billing_sessions
            await session.execute(
                text(
                    'UPDATE billing_sessions SET org_id = NULL WHERE org_id = :org_id'
                ),
                {'org_id': user_uuid},
            )

            # Step 6: Delete org_member entries for this org
            await session.execute(
                text('DELETE FROM org_member WHERE org_id = :org_id'),
                {'org_id': user_uuid},
            )

            # Step 7: Delete the user entry
            await session.execute(
                text('DELETE FROM "user" WHERE id = :user_id'),
                {'user_id': user_uuid},
            )

            # Delete the org entry
            await session.execute(
                text('DELETE FROM org WHERE id = :org_id'),
                {'org_id': user_uuid},
            )

            # Step 8: Set already_migrated=False on user_settings and encrypt fields
            user_settings.already_migrated = False

            # Re-encrypt the sensitive fields before storing in the DB
            encrypt_keys = [
                'llm_api_key',
                'llm_api_key_for_byor',
                'search_api_key',
                'sandbox_api_key',
            ]
            for key in encrypt_keys:
                value = getattr(user_settings, key, None)
                if value is not None and not _is_legacy_value_encrypted(value):
                    setattr(user_settings, key, encrypt_legacy_value(value))

            await session.merge(user_settings)

            await session.commit()

            logger.info(
                'user_store:downgrade_user:complete',
                extra={'user_id': user_id},
            )
            return user_settings
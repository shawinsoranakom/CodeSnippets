async def migrate_user(
        user_id: str,
        user_settings: UserSettings,
        user_info: dict,
    ) -> User | None:
        kwargs = decrypt_legacy_model(
            [
                'llm_api_key',
                'llm_api_key_for_byor',
                'search_api_key',
                'sandbox_api_key',
            ],
            user_settings,
        )
        decrypted_user_settings = UserSettings(**kwargs)
        async with a_session_maker() as session:
            # Check if user has completed billing sessions to enable BYOR export
            from storage.billing_session import BillingSession

            result = await session.execute(
                select(BillingSession).filter(
                    BillingSession.user_id == user_id,
                    BillingSession.status == 'completed',
                )
            )
            has_completed_billing = result.scalars().first() is not None

            # create personal org
            org = Org(
                id=uuid.UUID(user_id),
                name=f'user_{user_id}_org',
                org_version=user_settings.user_version,
                contact_name=resolve_display_name(user_info)
                or user_info.get('username', ''),
                contact_email=user_info['email'],
                byor_export_enabled=has_completed_billing,
            )
            session.add(org)

            from storage.lite_llm_manager import LiteLlmManager

            logger.debug(
                'user_store:migrate_user:calling_litellm_migrate_entries',
                extra={'user_id': user_id},
            )
            await LiteLlmManager.migrate_entries(
                str(org.id),
                user_id,
                decrypted_user_settings,
            )

            logger.debug(
                'user_store:migrate_user:done_litellm_migrate_entries',
                extra={'user_id': user_id},
            )
            custom_settings = UserStore._has_custom_settings(
                decrypted_user_settings, user_settings.user_version
            )

            # Migrate stripe customer (pass session to avoid FK violation)
            # avoids circular reference. This migrate method is temporary until all users are migrated.
            from integrations.stripe_service import migrate_customer

            logger.debug(
                'user_store:migrate_user:calling_stripe_migrate_customer',
                extra={'user_id': user_id},
            )
            await migrate_customer(session, user_id, org)
            logger.debug(
                'user_store:migrate_user:done_stripe_migrate_customer',
                extra={'user_id': user_id},
            )

            from storage.org_store import OrgStore

            org_kwargs = OrgStore.get_kwargs_from_user_settings(decrypted_user_settings)
            org_kwargs.pop('id', None)

            # If the user has custom settings, keep the org defaults minimal.
            if custom_settings:
                org_kwargs['agent_settings'] = {
                    'schema_version': AGENT_SETTINGS_SCHEMA_VERSION,
                    'llm': {
                        'model': get_default_litellm_model(),
                        'base_url': LITE_LLM_API_URL,
                    },
                }
                org_kwargs['org_version'] = ORG_SETTINGS_VERSION

            for key, value in org_kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)

            # Apply DEFAULT_V1_ENABLED for migrated orgs if v1_enabled was not set
            if org.v1_enabled is None:
                org.v1_enabled = DEFAULT_V1_ENABLED

            user_kwargs = UserStore.get_kwargs_from_user_settings(
                decrypted_user_settings
            )
            user_kwargs.pop('id', None)
            user = User(
                id=uuid.UUID(user_id),
                current_org_id=org.id,
                role_id=None,
                **user_kwargs,
            )
            session.add(user)

            logger.debug(
                'user_store:migrate_user:calling_get_role_by_name',
                extra={'user_id': user_id},
            )
            role = await RoleStore.get_role_by_name('owner')
            logger.debug(
                'user_store:migrate_user:done_get_role_by_name',
                extra={'user_id': user_id},
            )
            if role is None:
                raise ValueError('Owner role not found in database')

            from storage.org_member_store import OrgMemberStore

            org_member_kwargs = OrgMemberStore.get_kwargs_from_user_settings(
                decrypted_user_settings
            )
            if not custom_settings:
                org_member_kwargs['agent_settings_diff'] = (
                    OrgStore.get_agent_settings_from_org(org).model_dump(mode='json')
                )

            org_member = OrgMember(
                org_id=org.id,
                user_id=user.id,
                role_id=role.id,  # owner of your own org.
                status='active',
                **org_member_kwargs,
            )
            session.add(org_member)

            # Mark the old user_settings as migrated instead of deleting
            user_settings.already_migrated = True
            await session.merge(user_settings)
            await session.flush()
            logger.debug(
                'user_store:migrate_user:session_flush_complete',
                extra={'user_id': user_id},
            )

            user_uuid = uuid.UUID(user_id)

            # need to migrate conversation metadata
            await session.execute(
                text("""
                    INSERT INTO conversation_metadata_saas (conversation_id, user_id, org_id)
                    SELECT
                        conversation_id,
                        :user_uuid,
                        :user_uuid
                    FROM conversation_metadata
                    WHERE user_id = :user_id_text
                """),
                {'user_uuid': user_uuid, 'user_id_text': user_id},
            )

            # Update stripe_customers
            await session.execute(
                text(
                    'UPDATE stripe_customers SET org_id = :org_id WHERE keycloak_user_id = :user_id'
                ),
                {'org_id': user_uuid, 'user_id': user_id},
            )

            # Update slack_users
            await session.execute(
                text(
                    'UPDATE slack_users SET org_id = :org_id WHERE keycloak_user_id = :user_id'
                ),
                {'org_id': user_uuid, 'user_id': user_id},
            )

            # Update slack_conversation
            await session.execute(
                text(
                    'UPDATE slack_conversation SET org_id = :org_id WHERE keycloak_user_id = :user_id'
                ),
                {'org_id': user_uuid, 'user_id': user_id},
            )

            # Update api_keys
            await session.execute(
                text('UPDATE api_keys SET org_id = :org_id WHERE user_id = :user_id'),
                {'org_id': user_uuid, 'user_id': user_id},
            )

            # Update custom_secrets
            await session.execute(
                text(
                    'UPDATE custom_secrets SET org_id = :org_id WHERE keycloak_user_id = :user_id'
                ),
                {'org_id': user_uuid, 'user_id': user_id},
            )

            # Update billing_sessions
            await session.execute(
                text(
                    'UPDATE billing_sessions SET org_id = :org_id WHERE user_id = :user_id'
                ),
                {'org_id': user_uuid, 'user_id': user_id},
            )

            await session.commit()
            await session.refresh(user)
            await session.refresh(user, ['org_members'])  # load org_members
            logger.debug(
                'user_store:migrate_user:session_committed',
                extra={'user_id': user_id},
            )
            return user
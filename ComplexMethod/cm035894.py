async def patched_store(item):
        if item:
            # Make a copy of the item without email and email_verified
            item_dict = item.model_dump(context={'expose_secrets': True})
            item_dict['llm_api_key'] = _secret_value(item, 'llm.api_key')
            if 'email' in item_dict:
                del item_dict['email']
            if 'email_verified' in item_dict:
                del item_dict['email_verified']
            if 'secrets_store' in item_dict:
                del item_dict['secrets_store']

            # Encrypt the data before storing
            for key in ('llm_api_key', 'search_api_key', 'sandbox_api_key'):
                value = item_dict.get(key)
                if value is not None:
                    item_dict[key] = encrypt_legacy_value(value)
            item_dict['agent_settings'] = item.agent_settings.model_dump(
                mode='json', exclude_none=True
            )

            # Continue with the original implementation
            from sqlalchemy import select

            async with store.a_session_maker() as session:
                result = await session.execute(
                    select(UserSettings).filter(
                        UserSettings.keycloak_user_id == store.user_id
                    )
                )
                existing = result.scalars().first()

                if existing:
                    # Update existing entry
                    for key, value in item_dict.items():
                        if key in existing.__class__.__table__.columns:
                            setattr(existing, key, value)
                    await session.merge(existing)
                else:
                    item_dict['keycloak_user_id'] = store.user_id
                    settings = UserSettings(**item_dict)
                    session.add(settings)
                await session.commit()
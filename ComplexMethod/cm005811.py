async def test_load_bundles_from_urls():
    settings_service = get_settings_service()
    settings_service.settings.bundle_urls = [
        "https://github.com/langflow-ai/langflow-bundles/commit/68428ce16729a385fe1bcc0f1ec91fd5f5f420b9"
    ]
    settings_service.auth_settings.AUTO_LOGIN = True

    # Create a superuser in the test database since load_bundles_from_urls requires one
    async with session_scope() as session:
        await create_super_user(
            username=settings_service.auth_settings.SUPERUSER,
            password=(
                settings_service.auth_settings.SUPERUSER_PASSWORD.get_secret_value()
                if hasattr(settings_service.auth_settings.SUPERUSER_PASSWORD, "get_secret_value")
                else settings_service.auth_settings.SUPERUSER_PASSWORD
            ),
            db=session,
        )

    temp_dirs, components_paths = await load_bundles_from_urls()

    try:
        assert len(components_paths) == 1
        assert "langflow-bundles-68428ce16729a385fe1bcc0f1ec91fd5f5f420b9/components" in components_paths[0]

        content = await (Path(components_paths[0]) / "embeddings" / "openai2.py").read_text(encoding="utf-8")
        assert "OpenAIEmbeddings2Component" in content

        assert len(temp_dirs) == 1

        async with session_scope() as session:
            stmt = select(Flow).where(Flow.id == uuid.UUID("c54f9130-f2fa-4a3e-b22a-3856d946351b"))
            flow = (await session.exec(stmt)).first()
            assert flow is not None
    finally:
        for temp_dir in temp_dirs:
            await asyncio.to_thread(temp_dir.cleanup)
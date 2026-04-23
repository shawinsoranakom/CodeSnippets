async def test_mcp_with_legacy_folder_after_migration(self, client: AsyncClient):  # noqa: ARG002
        """Test that MCP finds migrated folders after setting custom DEFAULT_FOLDER_NAME."""
        user_id = uuid4()
        project_id = uuid4()
        flow_id = uuid4()

        # Only run this test when DEFAULT_FOLDER_NAME is set to custom value (e.g., "OpenRAG")
        if DEFAULT_FOLDER_NAME in ["Starter Project", "My Collection"]:
            pytest.skip("Test only applicable when DEFAULT_FOLDER_NAME is set to custom value")

        async with session_scope() as session:
            # Create user
            user = User(id=user_id, username=f"test_migrated_{user_id}", password="hashed_password")  # noqa: S106
            session.add(user)

            # Create folder with legacy name that will be migrated
            legacy_folder = Folder(id=project_id, name="Starter Project", user_id=user_id, description="Legacy folder")
            session.add(legacy_folder)

            # Create flow in folder
            flow = Flow(
                id=flow_id,
                name="Test Flow in Legacy Folder",
                description="A test flow",
                folder_id=project_id,
                user_id=user_id,
                is_component=False,
                mcp_enabled=None,
            )
            session.add(flow)

            await session.commit()

        try:
            # Trigger migration by calling get_or_create_default_folder
            from langflow.initial_setup.setup import get_or_create_default_folder

            async with session_scope() as session:
                migrated_folder = await get_or_create_default_folder(session, user_id)
                assert migrated_folder.name == DEFAULT_FOLDER_NAME
                assert migrated_folder.id == project_id  # Same folder, renamed

            # Now test that MCP can find the migrated folder
            async with session_scope() as session:
                from langflow.services.deps import get_settings_service

                settings_service = get_settings_service()
                original_setting = settings_service.settings.add_projects_to_mcp_servers

                try:
                    settings_service.settings.add_projects_to_mcp_servers = True
                    await auto_configure_starter_projects_mcp(session)

                    # Verify MCP found the migrated folder
                    updated_folder = await session.get(Folder, project_id)
                    assert updated_folder is not None
                    assert updated_folder.name == DEFAULT_FOLDER_NAME

                finally:
                    settings_service.settings.add_projects_to_mcp_servers = original_setting

        finally:
            # Cleanup
            async with session_scope() as session:
                flow_to_delete = await session.get(Flow, flow_id)
                if flow_to_delete:
                    await session.delete(flow_to_delete)
                folder_to_delete = await session.get(Folder, project_id)
                if folder_to_delete:
                    await session.delete(folder_to_delete)
                user_to_delete = await session.get(User, user_id)
                if user_to_delete:
                    await session.delete(user_to_delete)
                await session.commit()
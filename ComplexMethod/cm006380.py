async def create_or_update_agentic_flows(session: AsyncSession, user_id: UUID) -> None:
    """Create or update agentic flows in the Langflow Assistant folder for a user.

    This function is called on user login to ensure that all agentic flows
    are present and up-to-date in the user's Langflow Assistant folder.

    The function will:
    - Extract flow_id and endpoint_name from the JSON
    - Skip updates if flow already exists (only create new flows)
    - Create new flows if they don't exist

    Args:
        session: Database session
        user_id: The ID of the user
    """
    from lfx.services.deps import get_settings_service

    # Only configure if agentic experience is enabled
    settings_service = get_settings_service()
    if not settings_service.settings.agentic_experience:
        await logger.adebug("Agentic experience disabled, skipping agentic flows creation")
        return

    try:
        # Get or create the Langflow Assistant folder
        assistant_folder = await get_or_create_assistant_folder(session, user_id)

        # Load all agentic flows from the directory
        agentic_flows = await load_agentic_flows()

        if not agentic_flows:
            await logger.adebug("No agentic flows found to load")
            return

        flows_created = 0
        flows_updated = 0

        for _, flow_data in agentic_flows:
            # Extract flow metadata from JSON
            (
                flow_name,
                flow_description,
                flow_is_component,
                updated_at_datetime,
                project_data,
                flow_icon,
                flow_icon_bg_color,
                flow_gradient,
                flow_tags,
            ) = get_project_data(flow_data)

            # Extract flow_id and endpoint_name from JSON
            flow_id = flow_data.get("id")
            flow_endpoint_name = flow_data.get("endpoint_name")

            # Convert flow_id to UUID if it's a valid UUID string
            if flow_id and isinstance(flow_id, str):
                try:
                    flow_id = UUID(flow_id)
                except ValueError:
                    await logger.awarning(f"Invalid UUID for flow {flow_name}: {flow_id}, will use auto-generated ID")
                    flow_id = None

            # Try to find an existing flow by ID or endpoint_name
            existing_flow = await find_existing_flow(session, flow_id, flow_endpoint_name)

            if existing_flow:
                # Skip update if flow already exists
                await logger.adebug(f"Agentic flow already exists, skipping: {flow_name}")
                flows_updated += 1
            else:
                try:
                    await logger.adebug(f"Creating agentic flow: {flow_name}")
                    # Create new flow with ID and endpoint_name from JSON
                    new_project = FlowCreate(
                        name=flow_name,
                        description=flow_description,
                        icon=flow_icon,
                        icon_bg_color=flow_icon_bg_color,
                        data=project_data,
                        is_component=flow_is_component,
                        updated_at=updated_at_datetime,
                        folder_id=assistant_folder.id,
                        gradient=flow_gradient,
                        tags=flow_tags,
                        endpoint_name=flow_endpoint_name,  # Set endpoint_name from JSON
                    )
                    db_flow = Flow.model_validate(new_project.model_dump(exclude={"id"}))

                    # Set the ID from JSON if provided
                    if flow_id:
                        db_flow.id = flow_id

                    session.add(db_flow)
                    flows_created += 1
                except Exception:  # noqa: BLE001
                    await logger.aexception(f"Error while creating agentic flow {flow_name}")

        if flows_created > 0 or flows_updated > 0:
            await session.commit()
            await logger.adebug(
                f"Successfully created {flows_created} and skipped {flows_updated} existing agentic flows"
            )
        else:
            await logger.adebug("No agentic flows to create")

    except Exception:  # noqa: BLE001
        await logger.aexception("Error in create_or_update_agentic_flows")
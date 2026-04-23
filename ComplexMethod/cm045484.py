async def init_lite_mode(db_manager: DatabaseManager) -> None:
    """Initialize lite mode specific setup: load team and create default session"""
    if not is_lite_mode():
        return

    logger.info("Initializing lite mode...")

    # Load team from file (required in lite mode)
    if settings.LITE_TEAM_FILE and os.path.exists(settings.LITE_TEAM_FILE):
        try:
            # Import the team into the database
            result = await db_manager.import_team(settings.LITE_TEAM_FILE, settings.DEFAULT_USER_ID, check_exists=True)
            if result.status and result.data:
                team_id = result.data.get("id")
                logger.info(f"Loaded team from file {settings.LITE_TEAM_FILE} with ID: {team_id}")

                # Create a default session with this team
                from ..datamodel.db import Session

                session_name = settings.LITE_SESSION_NAME or "Lite Mode Session"

                session = Session(user_id=settings.DEFAULT_USER_ID, team_id=team_id, name=session_name)

                session_result = db_manager.upsert(session)
                if session_result.status and session_result.data:
                    session_id = session_result.data.get("id")
                    logger.info(f"Created lite mode session: {session_name} (ID: {session_id})")
                else:
                    logger.error(f"Failed to create session: {session_result.message}")
                    raise Exception(f"Failed to create session: {session_result.message}")
            else:
                logger.error(f"Failed to import team from file: {result.message}")
                raise Exception(f"Failed to import team: {result.message}")

        except Exception as e:
            logger.error(f"Failed to load team from file {settings.LITE_TEAM_FILE}: {str(e)}")
            raise
    else:
        logger.error("No team file specified for lite mode")
        raise Exception("Lite mode requires a team file to be specified")
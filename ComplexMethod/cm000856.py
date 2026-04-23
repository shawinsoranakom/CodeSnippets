async def get_chat_session(
    session_id: str,
    user_id: str | None = None,
) -> ChatSession | None:
    """Get a chat session by ID.

    Checks Redis cache first, falls back to database if not found.
    Caches database results back to Redis.

    Args:
        session_id: The session ID to fetch.
        user_id: If provided, validates that the session belongs to this user.
            If None, ownership is not validated (admin/system access).
    """
    # Try cache first
    try:
        session = await _get_session_from_cache(session_id)
        if session:
            # Verify user ownership if user_id was provided for validation
            if user_id is not None and session.user_id != user_id:
                logger.warning(
                    f"Session {session_id} user id mismatch: {session.user_id} != {user_id}"
                )
                return None
            return session
    except RedisError:
        logger.warning(f"Cache error for session {session_id}, trying database")
    except Exception as e:
        logger.warning(f"Unexpected cache error for session {session_id}: {e}")

    # Fall back to database
    logger.debug(f"Session {session_id} not in cache, checking database")
    session = await _get_session_from_db(session_id)

    if session is None:
        logger.warning(f"Session {session_id} not found in cache or database")
        return None

    # Verify user ownership if user_id was provided for validation
    if user_id is not None and session.user_id != user_id:
        logger.warning(
            f"Session {session_id} user id mismatch: {session.user_id} != {user_id}"
        )
        return None

    # Cache the session from DB
    try:
        await cache_chat_session(session)
        logger.info(f"Cached session {session_id} from database")
    except Exception as e:
        logger.warning(f"Failed to cache session {session_id}: {e}")

    return session
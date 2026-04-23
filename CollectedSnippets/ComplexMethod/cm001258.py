async def _log_vector_error_diagnostics(error: Exception) -> None:
    """Log diagnostic info when 'type vector does not exist' error occurs.

    Note: Diagnostic queries use query_raw_with_schema which may run on a different
    pooled connection than the one that failed. Session-level search_path can differ,
    so these diagnostics show cluster-wide state, not necessarily the failed session.

    Includes rate limiting to avoid log spam - only logs once per minute.
    Caller should re-raise the error after calling this function.
    """
    global _last_vector_diag_time

    # Check if this is the vector type error
    error_str = str(error).lower()
    if not (
        "type" in error_str and "vector" in error_str and "does not exist" in error_str
    ):
        return

    # Rate limit: only log once per interval
    now = time.time()
    if now - _last_vector_diag_time < _VECTOR_DIAG_INTERVAL_SECONDS:
        return
    _last_vector_diag_time = now

    try:
        diagnostics: dict[str, object] = {}

        try:
            search_path_result = await query_raw_with_schema("SHOW search_path")
            diagnostics["search_path"] = search_path_result
        except Exception as e:
            diagnostics["search_path"] = f"Error: {e}"

        try:
            schema_result = await query_raw_with_schema("SELECT current_schema()")
            diagnostics["current_schema"] = schema_result
        except Exception as e:
            diagnostics["current_schema"] = f"Error: {e}"

        try:
            user_result = await query_raw_with_schema(
                "SELECT current_user, session_user, current_database()"
            )
            diagnostics["user_info"] = user_result
        except Exception as e:
            diagnostics["user_info"] = f"Error: {e}"

        try:
            # Check pgvector extension installation (cluster-wide, stable info)
            ext_result = await query_raw_with_schema(
                "SELECT extname, extversion, nspname as schema "
                "FROM pg_extension e "
                "JOIN pg_namespace n ON e.extnamespace = n.oid "
                "WHERE extname = 'vector'"
            )
            diagnostics["pgvector_extension"] = ext_result
        except Exception as e:
            diagnostics["pgvector_extension"] = f"Error: {e}"

        logger.error(
            f"Vector type error diagnostics:\n"
            f"  Error: {error}\n"
            f"  search_path: {diagnostics.get('search_path')}\n"
            f"  current_schema: {diagnostics.get('current_schema')}\n"
            f"  user_info: {diagnostics.get('user_info')}\n"
            f"  pgvector_extension: {diagnostics.get('pgvector_extension')}"
        )
    except Exception as diag_error:
        logger.error(f"Failed to collect vector error diagnostics: {diag_error}")
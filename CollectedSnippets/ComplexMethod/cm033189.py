def set_logger_level():
    """Set log level for a package."""
    try:
        data = request.get_json()
        if not data or "pkg_name" not in data or "level" not in data:
            return error_response("pkg_name and level are required", 400)

        pkg_name = data["pkg_name"]
        level = data["level"]
        if not isinstance(pkg_name, str) or not isinstance(level, str):
            return error_response("pkg_name and level must be strings", 400)

        success = set_log_level(pkg_name, level)
        if success:
            return success_response({"pkg_name": pkg_name, "level": level}, "Log level updated successfully")
        else:
            return error_response(f"Invalid log level: {level}", 400)
    except Exception as e:
        return error_response(str(e), 500)
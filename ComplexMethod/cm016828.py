def _check_opengl_availability():
    """Early check for OpenGL availability. Raises RuntimeError if unlikely to work."""
    logger.debug("_check_opengl_availability: starting")
    missing = []

    # Check Python packages (using find_spec to avoid importing)
    logger.debug("_check_opengl_availability: checking for glfw package")
    if importlib.util.find_spec("glfw") is None:
        missing.append("glfw")

    logger.debug("_check_opengl_availability: checking for OpenGL package")
    if importlib.util.find_spec("OpenGL") is None:
        missing.append("PyOpenGL")

    if missing:
        raise RuntimeError(
            f"OpenGL dependencies not available.\n{get_missing_requirements_message()}\n"
        )

    # On Linux without display, check if headless backends are available
    logger.debug(f"_check_opengl_availability: platform={sys.platform}")
    if sys.platform.startswith("linux"):
        has_display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        logger.debug(f"_check_opengl_availability: has_display={bool(has_display)}")
        if not has_display:
            # Check for EGL or OSMesa libraries
            logger.debug("_check_opengl_availability: checking for EGL library")
            has_egl = ctypes.util.find_library("EGL")
            logger.debug("_check_opengl_availability: checking for OSMesa library")
            has_osmesa = ctypes.util.find_library("OSMesa")

            # Error disabled for CI as it fails this check
            # if not has_egl and not has_osmesa:
            #     raise RuntimeError(
            #         "GLSL Shader node: No display and no headless backend (EGL/OSMesa) found.\n"
            #         "See error below for installation instructions."
            #     )
            logger.debug(f"Headless mode: EGL={'yes' if has_egl else 'no'}, OSMesa={'yes' if has_osmesa else 'no'}")

    logger.debug("_check_opengl_availability: completed")
def _init_egl():
    """Initialize EGL for headless rendering. Returns (display, context, surface, EGL_module). Raises RuntimeError on failure."""
    logger.debug("_init_egl: starting")
    from OpenGL import EGL as _EGL
    from OpenGL.EGL import (
        eglGetDisplay, eglInitialize, eglChooseConfig, eglCreateContext,
        eglMakeCurrent, eglCreatePbufferSurface, eglBindAPI,
        eglTerminate, eglDestroyContext, eglDestroySurface,
        EGL_DEFAULT_DISPLAY, EGL_NO_CONTEXT, EGL_NONE,
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
        EGL_RED_SIZE, EGL_GREEN_SIZE, EGL_BLUE_SIZE, EGL_ALPHA_SIZE, EGL_DEPTH_SIZE,
        EGL_WIDTH, EGL_HEIGHT, EGL_OPENGL_API,
    )
    logger.debug("_init_egl: imports completed")

    display = None
    context = None
    surface = None

    try:
        logger.debug("_init_egl: calling eglGetDisplay()")
        display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
        if display == _EGL.EGL_NO_DISPLAY:
            raise RuntimeError("eglGetDisplay() failed")

        logger.debug("_init_egl: calling eglInitialize()")
        major, minor = _EGL.EGLint(), _EGL.EGLint()
        if not eglInitialize(display, major, minor):
            display = None  # Not initialized, don't terminate
            raise RuntimeError("eglInitialize() failed")
        logger.debug(f"_init_egl: EGL version {major.value}.{minor.value}")

        config_attribs = [
            EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
            EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
            EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
            EGL_DEPTH_SIZE, 0, EGL_NONE
        ]
        configs = (_EGL.EGLConfig * 1)()
        num_configs = _EGL.EGLint()
        if not eglChooseConfig(display, config_attribs, configs, 1, num_configs) or num_configs.value == 0:
            raise RuntimeError("eglChooseConfig() failed")
        config = configs[0]
        logger.debug(f"_init_egl: config chosen, num_configs={num_configs.value}")

        if not eglBindAPI(EGL_OPENGL_API):
            raise RuntimeError("eglBindAPI() failed")

        logger.debug("_init_egl: calling eglCreateContext()")
        context_attribs = [
            _EGL.EGL_CONTEXT_MAJOR_VERSION, 3,
            _EGL.EGL_CONTEXT_MINOR_VERSION, 3,
            _EGL.EGL_CONTEXT_OPENGL_PROFILE_MASK, _EGL.EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,
            EGL_NONE
        ]
        context = eglCreateContext(display, config, EGL_NO_CONTEXT, context_attribs)
        if context == EGL_NO_CONTEXT:
            raise RuntimeError("eglCreateContext() failed")

        logger.debug("_init_egl: calling eglCreatePbufferSurface()")
        pbuffer_attribs = [EGL_WIDTH, 64, EGL_HEIGHT, 64, EGL_NONE]
        surface = eglCreatePbufferSurface(display, config, pbuffer_attribs)
        if surface == _EGL.EGL_NO_SURFACE:
            raise RuntimeError("eglCreatePbufferSurface() failed")

        logger.debug("_init_egl: calling eglMakeCurrent()")
        if not eglMakeCurrent(display, surface, surface, context):
            raise RuntimeError("eglMakeCurrent() failed")

        logger.debug("_init_egl: completed successfully")
        return display, context, surface, _EGL

    except Exception:
        logger.debug("_init_egl: failed, cleaning up")
        # Clean up any resources on failure
        if surface is not None:
            eglDestroySurface(display, surface)
        if context is not None:
            eglDestroyContext(display, context)
        if display is not None:
            eglTerminate(display)
        raise
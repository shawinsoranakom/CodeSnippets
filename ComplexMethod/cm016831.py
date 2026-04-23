def __init__(self):
        if GLContext._initialized:
            logger.debug("GLContext.__init__: already initialized, skipping")
            return

        logger.debug("GLContext.__init__: starting initialization")

        global glfw, EGL

        import time
        start = time.perf_counter()

        self._backend = None
        self._window = None
        self._egl_display = None
        self._egl_context = None
        self._egl_surface = None
        self._osmesa_ctx = None
        self._osmesa_buffer = None
        self._vao = None

        # Try backends in order: GLFW → EGL → OSMesa
        errors = []

        logger.debug("GLContext.__init__: trying GLFW backend")
        try:
            self._window, glfw = _init_glfw()
            self._backend = "glfw"
            logger.debug("GLContext.__init__: GLFW backend succeeded")
        except Exception as e:
            logger.debug(f"GLContext.__init__: GLFW backend failed: {e}")
            errors.append(("GLFW", e))

        if self._backend is None:
            logger.debug("GLContext.__init__: trying EGL backend")
            try:
                self._egl_display, self._egl_context, self._egl_surface, EGL = _init_egl()
                self._backend = "egl"
                logger.debug("GLContext.__init__: EGL backend succeeded")
            except Exception as e:
                logger.debug(f"GLContext.__init__: EGL backend failed: {e}")
                errors.append(("EGL", e))

        if self._backend is None:
            logger.debug("GLContext.__init__: trying OSMesa backend")
            try:
                self._osmesa_ctx, self._osmesa_buffer = _init_osmesa()
                self._backend = "osmesa"
                logger.debug("GLContext.__init__: OSMesa backend succeeded")
            except Exception as e:
                logger.debug(f"GLContext.__init__: OSMesa backend failed: {e}")
                errors.append(("OSMesa", e))

        if self._backend is None:
            if sys.platform == "win32":
                platform_help = (
                    "Windows: Ensure GPU drivers are installed and display is available.\n"
                    "         CPU-only/headless mode is not supported on Windows."
                )
            elif sys.platform == "darwin":
                platform_help = (
                    "macOS: GLFW is not supported.\n"
                    "  Install OSMesa via Homebrew: brew install mesa\n"
                    "  Then: pip install PyOpenGL PyOpenGL-accelerate"
                )
            else:
                platform_help = (
                    "Linux: Install one of these backends:\n"
                    "  Desktop:           sudo apt install libgl1-mesa-glx libglfw3\n"
                    "  Headless with GPU: sudo apt install libegl1-mesa libgl1-mesa-dri\n"
                    "  Headless (CPU):    sudo apt install libosmesa6"
                )

            error_details = "\n".join(f"  {name}: {err}" for name, err in errors)
            raise RuntimeError(
                f"Failed to create OpenGL context.\n\n"
                f"Backend errors:\n{error_details}\n\n"
                f"{platform_help}"
            )

        # Now import OpenGL.GL (after context is current)
        logger.debug("GLContext.__init__: importing OpenGL.GL")
        _import_opengl()

        # Create VAO (required for core profile, but OSMesa may use compat profile)
        logger.debug("GLContext.__init__: creating VAO")
        try:
            vao = gl.glGenVertexArrays(1)
            gl.glBindVertexArray(vao)
            self._vao = vao  # Only store after successful bind
            logger.debug("GLContext.__init__: VAO created successfully")
        except Exception as e:
            logger.debug(f"GLContext.__init__: VAO creation failed (may be expected for OSMesa): {e}")
            # OSMesa with older Mesa may not support VAOs
            # Clean up if we created but couldn't bind
            if vao:
                try:
                    gl.glDeleteVertexArrays(1, [vao])
                except Exception:
                    pass

        elapsed = (time.perf_counter() - start) * 1000

        # Log device info
        renderer = gl.glGetString(gl.GL_RENDERER)
        vendor = gl.glGetString(gl.GL_VENDOR)
        version = gl.glGetString(gl.GL_VERSION)
        renderer = renderer.decode() if renderer else "Unknown"
        vendor = vendor.decode() if vendor else "Unknown"
        version = version.decode() if version else "Unknown"

        GLContext._initialized = True
        logger.info(f"GLSL context initialized in {elapsed:.1f}ms ({self._backend}) - {renderer} ({vendor}), GL {version}")
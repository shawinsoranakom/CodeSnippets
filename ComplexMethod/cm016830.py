def _render_shader_batch(
    fragment_code: str,
    width: int,
    height: int,
    image_batches: list[list[np.ndarray]],
    floats: list[float],
    ints: list[int],
    bools: list[bool] | None = None,
    curves: list[np.ndarray] | None = None,
) -> list[list[np.ndarray]]:
    """
    Render a fragment shader for multiple batches efficiently.

    Compiles shader once, reuses framebuffer/textures across batches.
    Supports multi-pass rendering via #pragma passes N directive.

    Args:
        fragment_code: User's fragment shader code
        width: Output width
        height: Output height
        image_batches: List of batches, each batch is a list of input images (H, W, C) float32 [0,1]
        floats: List of float uniforms
        ints: List of int uniforms
        bools: List of bool uniforms (passed as int 0/1 to GLSL bool uniforms)
        curves: List of 1D LUT arrays (float32) of arbitrary size for u_curve0-N

    Returns:
        List of batch outputs, each is a list of output images (H, W, 4) float32 [0,1]
    """
    import time
    start_time = time.perf_counter()

    if not image_batches:
        return []

    ctx = GLContext()
    ctx.make_current()

    # Convert from GLSL ES to desktop GLSL 330
    fragment_source = _convert_es_to_desktop(fragment_code)

    # Detect how many outputs the shader actually uses
    num_outputs = _detect_output_count(fragment_code)

    # Detect multi-pass rendering
    num_passes = _detect_pass_count(fragment_code)

    if bools is None:
        bools = []
    if curves is None:
        curves = []

    # Track resources for cleanup
    program = None
    fbo = None
    output_textures = []
    input_textures = []
    curve_textures = []
    ping_pong_textures = []
    ping_pong_fbos = []

    num_inputs = len(image_batches[0])

    try:
        # Compile shaders (once for all batches)
        try:
            program = _create_program(VERTEX_SHADER, fragment_source)
        except RuntimeError:
            logger.error(f"Fragment shader:\n{fragment_source}")
            raise

        gl.glUseProgram(program)

        # Create framebuffer with only the needed color attachments
        fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)

        draw_buffers = []
        for i in range(num_outputs):
            tex = gl.glGenTextures(1)
            output_textures.append(tex)
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, width, height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0 + i, gl.GL_TEXTURE_2D, tex, 0)
            draw_buffers.append(gl.GL_COLOR_ATTACHMENT0 + i)

        gl.glDrawBuffers(num_outputs, draw_buffers)

        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer is not complete")

        # Create ping-pong resources for multi-pass rendering
        if num_passes > 1:
            for _ in range(2):
                pp_tex = gl.glGenTextures(1)
                ping_pong_textures.append(pp_tex)
                gl.glBindTexture(gl.GL_TEXTURE_2D, pp_tex)
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, width, height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

                pp_fbo = gl.glGenFramebuffers(1)
                ping_pong_fbos.append(pp_fbo)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, pp_fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, pp_tex, 0)
                gl.glDrawBuffers(1, [gl.GL_COLOR_ATTACHMENT0])

                if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
                    raise RuntimeError("Ping-pong framebuffer is not complete")

        # Create input textures (reused for all batches)
        for i in range(num_inputs):
            tex = gl.glGenTextures(1)
            input_textures.append(tex)
            gl.glActiveTexture(gl.GL_TEXTURE0 + i)
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

            loc = gl.glGetUniformLocation(program, f"u_image{i}")
            if loc >= 0:
                gl.glUniform1i(loc, i)

        # Set static uniforms (once for all batches)
        loc = gl.glGetUniformLocation(program, "u_resolution")
        if loc >= 0:
            gl.glUniform2f(loc, float(width), float(height))

        for i, v in enumerate(floats):
            loc = gl.glGetUniformLocation(program, f"u_float{i}")
            if loc >= 0:
                gl.glUniform1f(loc, v)

        for i, v in enumerate(ints):
            loc = gl.glGetUniformLocation(program, f"u_int{i}")
            if loc >= 0:
                gl.glUniform1i(loc, v)

        for i, v in enumerate(bools):
            loc = gl.glGetUniformLocation(program, f"u_bool{i}")
            if loc >= 0:
                gl.glUniform1i(loc, 1 if v else 0)

        # Create 1D LUT textures for curves (bound after image texture units)
        for i, lut in enumerate(curves):
            tex = gl.glGenTextures(1)
            curve_textures.append(tex)
            unit = MAX_IMAGES + i
            gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_R32F, len(lut), 1, 0, gl.GL_RED, gl.GL_FLOAT, lut)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

            loc = gl.glGetUniformLocation(program, f"u_curve{i}")
            if loc >= 0:
                gl.glUniform1i(loc, unit)

        # Get u_pass uniform location for multi-pass
        pass_loc = gl.glGetUniformLocation(program, "u_pass")

        gl.glViewport(0, 0, width, height)
        gl.glDisable(gl.GL_BLEND)  # Ensure no alpha blending - write output directly

        # Process each batch
        all_batch_outputs = []
        for images in image_batches:
            # Update input textures with this batch's images
            for i, img in enumerate(images):
                gl.glActiveTexture(gl.GL_TEXTURE0 + i)
                gl.glBindTexture(gl.GL_TEXTURE_2D, input_textures[i])

                # Flip vertically for GL coordinates, ensure RGBA
                h, w, c = img.shape
                if c == 3:
                    img_upload = np.empty((h, w, 4), dtype=np.float32)
                    img_upload[:, :, :3] = img[::-1, :, :]
                    img_upload[:, :, 3] = 1.0
                else:
                    img_upload = np.ascontiguousarray(img[::-1, :, :])

                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, w, h, 0, gl.GL_RGBA, gl.GL_FLOAT, img_upload)

            if num_passes == 1:
                # Single pass - render directly to output FBO
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
                if pass_loc >= 0:
                    gl.glUniform1i(pass_loc, 0)
                gl.glClearColor(0, 0, 0, 0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
                gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
            else:
                # Multi-pass rendering with ping-pong
                for p in range(num_passes):
                    is_last_pass = (p == num_passes - 1)

                    # Set pass uniform
                    if pass_loc >= 0:
                        gl.glUniform1i(pass_loc, p)

                    if is_last_pass:
                        # Last pass renders to the main output FBO
                        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
                    else:
                        # Intermediate passes render to ping-pong FBO
                        target_fbo = ping_pong_fbos[p % 2]
                        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, target_fbo)

                    # Set input texture for this pass
                    gl.glActiveTexture(gl.GL_TEXTURE0)
                    if p == 0:
                        # First pass reads from original input
                        gl.glBindTexture(gl.GL_TEXTURE_2D, input_textures[0])
                    else:
                        # Subsequent passes read from previous pass output
                        source_tex = ping_pong_textures[(p - 1) % 2]
                        gl.glBindTexture(gl.GL_TEXTURE_2D, source_tex)

                    gl.glClearColor(0, 0, 0, 0)
                    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
                    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

            # Read back outputs for this batch
            # (glGetTexImage is synchronous, implicitly waits for rendering)
            batch_outputs = []
            for tex in output_textures:
                gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
                data = gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, gl.GL_FLOAT)
                img = np.frombuffer(data, dtype=np.float32).reshape(height, width, 4)
                batch_outputs.append(img[::-1, :, :].copy())

            # Pad with black images for unused outputs
            black_img = np.zeros((height, width, 4), dtype=np.float32)
            for _ in range(num_outputs, MAX_OUTPUTS):
                batch_outputs.append(black_img)

            all_batch_outputs.append(batch_outputs)

        elapsed = (time.perf_counter() - start_time) * 1000
        num_batches = len(image_batches)
        pass_info = f", {num_passes} passes" if num_passes > 1 else ""
        logger.info(f"GLSL shader executed in {elapsed:.1f}ms ({num_batches} batch{'es' if num_batches != 1 else ''}, {width}x{height}{pass_info})")

        return all_batch_outputs

    finally:
        # Unbind before deleting
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glUseProgram(0)

        for tex in input_textures:
            gl.glDeleteTextures(int(tex))
        for tex in curve_textures:
            gl.glDeleteTextures(int(tex))
        for tex in output_textures:
            gl.glDeleteTextures(int(tex))
        for tex in ping_pong_textures:
            gl.glDeleteTextures(int(tex))
        if fbo is not None:
            gl.glDeleteFramebuffers(1, [fbo])
        for pp_fbo in ping_pong_fbos:
            gl.glDeleteFramebuffers(1, [pp_fbo])
        if program is not None:
            gl.glDeleteProgram(program)
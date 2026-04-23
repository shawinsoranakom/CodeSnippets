def init_window(self, title: str, fps: int = _DEFAULT_FPS):
    with self._startup_profile_context():
      def _close(sig, frame):
        self.close()
        sys.exit(0)
      signal.signal(signal.SIGINT, _close)
      atexit.register(self.close)

      flags = rl.ConfigFlags.FLAG_MSAA_4X_HINT
      if ENABLE_VSYNC:
        flags |= rl.ConfigFlags.FLAG_VSYNC_HINT
      rl.set_config_flags(flags)

      rl.init_window(self._scaled_width, self._scaled_height, title)

      needs_render_texture = self._scale != 1.0 or BURN_IN_MODE or RECORD
      if self._scale != 1.0:
        rl.set_mouse_scale(1 / self._scale, 1 / self._scale)
      if needs_render_texture:
        self._render_texture = rl.load_render_texture(self._scaled_width, self._scaled_height)
        rl.set_texture_filter(self._render_texture.texture, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)

      if RECORD:
        output_fps = fps * RECORD_SPEED
        ffmpeg_args = [
          'ffmpeg',
          '-v', 'warning',          # Reduce ffmpeg log spam
          '-nostats',               # Suppress encoding progress
          '-f', 'rawvideo',         # Input format
          '-pix_fmt', 'rgba',       # Input pixel format
          '-s', f'{self._scaled_width}x{self._scaled_height}',  # Input resolution
          '-r', str(fps),           # Input frame rate
          '-i', 'pipe:0',           # Input from stdin
          '-vf', 'vflip,format=yuv420p',  # Flip vertically and convert to yuv420p
          '-r', str(output_fps),    # Output frame rate (for speed multiplier)
          '-c:v', 'libx264',
          '-preset', 'veryfast',
          '-crf', str(RECORD_QUALITY)
        ]
        if RECORD_BITRATE:
          # NOTE: custom bitrate overrides crf setting
          ffmpeg_args += ['-b:v', RECORD_BITRATE, '-maxrate', RECORD_BITRATE, '-bufsize', RECORD_BITRATE]
        ffmpeg_args += [
          '-y',                     # Overwrite existing file
          '-f', 'mp4',              # Output format
          RECORD_OUTPUT,            # Output file path
        ]
        self._ffmpeg_proc = subprocess.Popen(ffmpeg_args, stdin=subprocess.PIPE)
        self._ffmpeg_queue = queue.Queue(maxsize=60)  # Buffer up to 60 frames
        self._ffmpeg_stop_event = threading.Event()
        self._ffmpeg_thread = threading.Thread(target=self._ffmpeg_writer_thread, daemon=True)
        self._ffmpeg_thread.start()

      # OFFSCREEN disables FPS limiting for fast offline rendering (e.g. clips)
      rl.set_target_fps(0 if OFFSCREEN else fps)

      self._target_fps = fps
      self._set_styles()
      self._load_fonts()
      self._patch_text_functions()
      self._patch_scissor_mode()
      if BURN_IN_MODE and self._burn_in_shader is None:
        self._burn_in_shader = rl.load_shader_from_memory(BURN_IN_VERTEX_SHADER, BURN_IN_FRAGMENT_SHADER)

      if not PC:
        self._mouse.start()
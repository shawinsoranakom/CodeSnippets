def update_frame(self, dt: float = 0, force_draw: bool = False) -> None:
        self.increment_time(dt)
        self.update_mobjects(dt)
        if self.skip_animations and not force_draw:
            return

        if self.is_window_closing():
            raise EndScene()

        if self.window and dt == 0 and not self.window.has_undrawn_event() and not force_draw:
            # In this case, there's no need for new rendering, but we
            # shoudl still listen for new events
            self.window._window.dispatch_events()
            return

        self.camera.capture(*self.render_groups)

        if self.window and not self.skip_animations:
            vt = self.time - self.virtual_animation_start_time
            rt = time.time() - self.real_animation_start_time
            time.sleep(max(vt - rt, 0))
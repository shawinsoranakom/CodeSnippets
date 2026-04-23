def on_key_press(
        self,
        symbol: int,
        modifiers: int
    ) -> None:
        try:
            char = chr(symbol)
        except OverflowError:
            log.warning("The value of the pressed key is too large.")
            return

        event_data = {"symbol": symbol, "modifiers": modifiers}
        propagate_event = EVENT_DISPATCHER.dispatch(EventType.KeyPressEvent, **event_data)
        if propagate_event is not None and propagate_event is False:
            return

        if char == manim_config.key_bindings.reset:
            self.play(self.camera.frame.animate.to_default_state())
        elif char == "z" and (modifiers & (PygletWindowKeys.MOD_COMMAND | PygletWindowKeys.MOD_CTRL)):
            self.undo()
        elif char == "z" and (modifiers & (PygletWindowKeys.MOD_COMMAND | PygletWindowKeys.MOD_CTRL | PygletWindowKeys.MOD_SHIFT)):
            self.redo()
        # command + q
        elif char == manim_config.key_bindings.quit and (modifiers & (PygletWindowKeys.MOD_COMMAND | PygletWindowKeys.MOD_CTRL)):
            self.quit_interaction = True
        # Space or right arrow
        elif char == " " or symbol == PygletWindowKeys.RIGHT:
            self.hold_on_wait = False
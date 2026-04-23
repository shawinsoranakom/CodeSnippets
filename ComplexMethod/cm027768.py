def on_key_press(self, mob: Mobject, event_data: dict[str, int]) -> bool | None:
        symbol = event_data["symbol"]
        modifiers = event_data["modifiers"]
        char = chr(symbol)
        if mob.isActive:
            old_value = mob.get_value()
            new_value = old_value
            if char.isalnum():
                if (modifiers & PygletWindowKeys.MOD_SHIFT) or (modifiers & PygletWindowKeys.MOD_CAPSLOCK):
                    new_value = old_value + char.upper()
                else:
                    new_value = old_value + char.lower()
            elif symbol in [PygletWindowKeys.SPACE]:
                new_value = old_value + char
            elif symbol == PygletWindowKeys.TAB:
                new_value = old_value + '\t'
            elif symbol == PygletWindowKeys.BACKSPACE:
                new_value = old_value[:-1] or ''
            mob.set_value(new_value)
            return False
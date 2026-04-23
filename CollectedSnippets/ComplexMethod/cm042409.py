def __init__(self, auto_return_to_letters: str = ""):
    super().__init__()
    self._auto_return_to_letters = auto_return_to_letters

    lower_chars = [
      "qwertyuiop",
      "asdfghjkl",
      "zxcvbnm",
    ]
    upper_chars = ["".join([char.upper() for char in row]) for row in lower_chars]
    special_chars = [
      "1234567890",
      "-/:;()$&@\"",
      "~.,?!'#%",
    ]
    super_special_chars = [
      "1234567890",
      "`[]{}^*+=_",
      "\\|<>¥€£•",
    ]

    self._lower_keys = [[Key(char) for char in row] for row in lower_chars]
    self._upper_keys = [[Key(char) for char in row] for row in upper_chars]
    self._special_keys = [[Key(char) for char in row] for row in special_chars]
    self._super_special_keys = [[Key(char) for char in row] for row in super_special_chars]

    # control keys
    self._space_key = IconKey("icons_mici/settings/keyboard/space.png", char=" ", vertical_align="bottom", icon_size=(43, 14))
    self._caps_key = IconKey("icons_mici/settings/keyboard/caps_lower.png", icon_size=(38, 33))
    # these two are in different places on some layouts
    self._123_key, self._123_key2 = SmallKey("123"), SmallKey("123")
    self._abc_key = SmallKey("abc")
    self._super_special_key = SmallKey("#+=")

    # insert control keys
    for keys in (self._lower_keys, self._upper_keys):
      keys[2].insert(0, self._caps_key)
      keys[2].append(self._123_key)

    for keys in (self._lower_keys, self._upper_keys, self._special_keys, self._super_special_keys):
      keys[1].append(self._space_key)

    for keys in (self._special_keys, self._super_special_keys):
      keys[2].append(self._abc_key)

    self._special_keys[2].insert(0, self._super_special_key)
    self._super_special_keys[2].insert(0, self._123_key2)

    # set initial keys
    self._current_keys: list[list[Key]] = []
    self._set_keys(self._lower_keys)
    self._caps_state = CapsState.LOWER
    self._initialized = False

    self._load_images()

    self._closest_key: tuple[Key | None, float] = None, float('inf')
    self._selected_key_t: float | None = None  # time key was initially selected
    self._unselect_key_t: float | None = None  # time to unselect key after release
    self._dragging_on_keyboard = False

    self._text: str = ""

    self._bg_scale_filter = BounceFilter(1.0, 0.1 * ANIMATION_SCALE, 1 / gui_app.target_fps)
    self._selected_key_filter = FirstOrderFilter(0.0, 0.075 * ANIMATION_SCALE, 1 / gui_app.target_fps)
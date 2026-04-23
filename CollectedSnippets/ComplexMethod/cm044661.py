def _detect_color_system(self) -> Optional[ColorSystem]:
        """Detect color system from env vars."""
        if self.is_jupyter:
            return ColorSystem.TRUECOLOR
        if not self.is_terminal or self.is_dumb_terminal:
            return None
        if WINDOWS:  # pragma: no cover
            if self.legacy_windows:  # pragma: no cover
                return ColorSystem.WINDOWS
            windows_console_features = get_windows_console_features()
            return (
                ColorSystem.TRUECOLOR
                if windows_console_features.truecolor
                else ColorSystem.EIGHT_BIT
            )
        else:
            color_term = self._environ.get("COLORTERM", "").strip().lower()
            if color_term in ("truecolor", "24bit"):
                return ColorSystem.TRUECOLOR
            term = self._environ.get("TERM", "").strip().lower()
            _term_name, _hyphen, colors = term.rpartition("-")
            color_system = _TERM_COLORS.get(colors, ColorSystem.STANDARD)
            return color_system
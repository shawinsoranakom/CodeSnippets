def create_api_model(self):
        if self.colors is None and self.background_color is None and self.artistic_level is None and self.no_text is None:
            return None
        colors_api = None
        background_color_api = None
        if self.colors:
            colors_api = self.colors.create_api_model()
        if self.background_color:
            first_background = self.background_color.get_first()
            background_color_api = first_background.create_api_model() if first_background else None

        return RecraftControlsObject(colors=colors_api, background_color=background_color_api,
                                             artistic_level=self.artistic_level, no_text=self.no_text)
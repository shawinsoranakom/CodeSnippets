def _media(self):
                return super().media + Media(
                    css={"all": ("/other/path",)}, js=("/other/js",)
                )
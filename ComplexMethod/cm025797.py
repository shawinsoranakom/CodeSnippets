def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend, if any."""
        if (
            self.entity_description.key is HabiticaSensorEntity.CLASS
            and self.user is not None
            and (_class := self.user.stats.Class)
        ):
            return SVG_CLASS[_class]

        if (
            self.entity_description.key is HabiticaSensorEntity.DISPLAY_NAME
            and self.user is not None
            and (img_url := self.user.profile.imageUrl)
        ):
            return img_url

        if entity_picture := self.entity_description.entity_picture:
            return (
                entity_picture
                if entity_picture.startswith("data:image")
                else f"{ASSETS_URL}{entity_picture}"
            )

        return None
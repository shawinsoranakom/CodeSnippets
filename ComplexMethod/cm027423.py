async def async_process_image(self, image: bytes) -> None:
        """Process image.

        This method is a coroutine.
        """
        face_data = None
        try:
            face_data = await self._api.call_api(
                "post",
                "detect",
                image,
                binary=True,
                params={"returnFaceAttributes": ",".join(self._attributes)},
            )

        except HomeAssistantError as err:
            _LOGGER.error("Can't process image on microsoft face: %s", err)
            return

        if not face_data:
            face_data = []

        faces: list[FaceInformation] = []
        for face in face_data:
            face_attr = FaceInformation()
            for attr in self._attributes:
                if TYPE_CHECKING:
                    assert attr in SUPPORTED_ATTRIBUTES
                if attr in face["faceAttributes"]:
                    face_attr[attr] = face["faceAttributes"][attr]  # type: ignore[literal-required]

            if face_attr:
                faces.append(face_attr)

        self.async_process_faces(faces, len(face_data))
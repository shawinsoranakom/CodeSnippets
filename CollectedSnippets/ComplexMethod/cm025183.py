async def async_process_image(self, image: bytes) -> None:
        """Process image.

        This method is a coroutine.
        """
        detect = []
        try:
            face_data = await self._api.call_api("post", "detect", image, binary=True)

            if face_data:
                face_ids = [data["faceId"] for data in face_data]
                detect = await self._api.call_api(
                    "post",
                    "identify",
                    {"faceIds": face_ids, "personGroupId": self._face_group},
                )

        except HomeAssistantError as err:
            _LOGGER.error("Can't process image on Microsoft face: %s", err)
            return

        # Parse data
        known_faces: list[FaceInformation] = []
        total = 0
        for face in detect:
            total += 1
            if not face["candidates"]:
                continue

            data = face["candidates"][0]
            name = ""
            for s_name, s_id in self._api.store[self._face_group].items():
                if data["personId"] == s_id:
                    name = s_name
                    break

            known_faces.append(
                {ATTR_NAME: name, ATTR_CONFIDENCE: data["confidence"] * 100}
            )

        self.async_process_faces(known_faces, total)
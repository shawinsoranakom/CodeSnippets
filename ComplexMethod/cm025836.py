def process_image(self, image: bytes) -> None:
        """Process the image."""
        try:
            img = Image.open(io.BytesIO(bytearray(image))).convert("RGB")
        except UnidentifiedImageError:
            _LOGGER.warning("Unable to process image, bad data")
            return
        img_width, img_height = img.size

        if self._aspect and abs((img_width / img_height) - self._aspect) > 0.1:
            _LOGGER.debug(
                (
                    "The image aspect: %s and the detector aspect: %s differ by more"
                    " than 0.1"
                ),
                (img_width / img_height),
                self._aspect,
            )

        # Run detection
        start = time.monotonic()
        response = self._doods.detect(
            image, dconfig=self._dconfig, detector_name=self._detector_name
        )
        _LOGGER.debug(
            "doods detect: %s response: %s duration: %s",
            self._dconfig,
            response,
            time.monotonic() - start,
        )

        matches: dict[str, list[dict[str, Any]]] = {}
        total_matches = 0

        if not response or "error" in response:
            if "error" in response:
                _LOGGER.error(response["error"])
            self._matches = matches
            self._total_matches = total_matches
            self._process_time = time.monotonic() - start
            return

        for detection in response["detections"]:
            score = detection["confidence"]
            boxes = [
                detection["top"],
                detection["left"],
                detection["bottom"],
                detection["right"],
            ]
            label = detection["label"]

            # Exclude unlisted labels
            if "*" not in self._dconfig and label not in self._dconfig:
                continue

            # Exclude matches outside global area definition
            if self._covers:
                if (
                    boxes[0] < self._area[0]
                    or boxes[1] < self._area[1]
                    or boxes[2] > self._area[2]
                    or boxes[3] > self._area[3]
                ):
                    continue
            elif (
                boxes[0] > self._area[2]
                or boxes[1] > self._area[3]
                or boxes[2] < self._area[0]
                or boxes[3] < self._area[1]
            ):
                continue

            # Exclude matches outside label specific area definition
            if self._label_areas.get(label):
                if self._label_covers[label]:
                    if (
                        boxes[0] < self._label_areas[label][0]
                        or boxes[1] < self._label_areas[label][1]
                        or boxes[2] > self._label_areas[label][2]
                        or boxes[3] > self._label_areas[label][3]
                    ):
                        continue
                elif (
                    boxes[0] > self._label_areas[label][2]
                    or boxes[1] > self._label_areas[label][3]
                    or boxes[2] < self._label_areas[label][0]
                    or boxes[3] < self._label_areas[label][1]
                ):
                    continue

            if label not in matches:
                matches[label] = []
            matches[label].append({"score": float(score), "box": boxes})
            total_matches += 1

        # Save Images
        if total_matches and self._file_out:
            paths = []
            for path_template in self._file_out:
                if isinstance(path_template, template.Template):
                    paths.append(path_template.render(camera_entity=self.camera_entity))
                else:
                    paths.append(path_template)
            self._save_image(image, matches, paths)
        else:
            _LOGGER.debug(
                "Not saving image(s), no detections found or no output file configured"
            )

        self._matches = matches
        self._total_matches = total_matches
        self._process_time = time.monotonic() - start
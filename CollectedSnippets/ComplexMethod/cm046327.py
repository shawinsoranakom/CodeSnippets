def verbose(self) -> str:
        """Return a log string for each task in the results, detailing detection and classification outcomes.

        This method generates a human-readable string summarizing the detection and classification results. It includes
        the number of detections for each class and the top probabilities for classification tasks.

        Returns:
            (str): A formatted string containing a summary of the results. For detection tasks, it includes the number
                of detections per class. For classification tasks, it includes the top 5 class probabilities.

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> for result in results:
            ...     print(result.verbose())
            2 persons, 1 car, 3 traffic lights,
            dog 0.92, cat 0.78, horse 0.64,

        Notes:
            - If there are no detections, the method returns "(no detections), " for detection tasks.
            - For classification tasks, it returns the top 5 class probabilities and their corresponding class names.
            - The returned string is comma-separated and ends with a comma and a space.
        """
        boxes = self.obb if self.obb is not None else self.boxes
        if len(self) == 0:
            return "" if self.probs is not None else "(no detections), "
        if self.probs is not None:
            return f"{', '.join(f'{self.names[j]} {self.probs.data[j]:.2f}' for j in self.probs.top5)}, "
        if boxes:
            counts = boxes.cls.int().bincount()
            return "".join(f"{n} {self.names[i]}{'s' * (n > 1)}, " for i, n in enumerate(counts) if n > 0)
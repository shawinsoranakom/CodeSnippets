def _evaluate_table_orientation(self, table_img, sample_ratio=0.3):
        """
        Evaluate the best rotation orientation for a table image.

        Tests 4 rotation angles (0°, 90°, 180°, 270°) and uses OCR
        confidence scores to determine the best orientation.

        Args:
            table_img: PIL Image object of the table region
            sample_ratio: Sampling ratio for quick evaluation

        Returns:
            tuple: (best_angle, best_img, confidence_scores)
                - best_angle: Best rotation angle (0, 90, 180, 270)
                - best_img: Image rotated to best orientation
                - confidence_scores: Dict of scores for each angle
        """

        rotations = [
            (0, "original"),
            (90, "rotate_90"),  # clockwise 90°
            (180, "rotate_180"),  # 180°
            (270, "rotate_270"),  # clockwise 270° (counter-clockwise 90°)
        ]

        results = {}
        best_score = -1
        best_angle = 0
        best_img = table_img
        score_0 = None

        for angle, name in rotations:
            # Rotate image
            if angle == 0:
                rotated_img = table_img
            else:
                # PIL's rotate is counter-clockwise, use negative angle for clockwise
                rotated_img = table_img.rotate(-angle, expand=True)

            # Convert to numpy array for OCR
            img_array = np.array(rotated_img)

            # Perform OCR detection and recognition
            try:
                ocr_results = self.ocr(img_array)

                if ocr_results:
                    # Calculate average confidence
                    scores = [conf for _, (_, conf) in ocr_results]
                    avg_score = sum(scores) / len(scores) if scores else 0
                    total_regions = len(scores)

                    # Combined score: considers both average confidence and number of regions
                    # More regions + higher confidence = better orientation
                    combined_score = avg_score * (1 + 0.1 * min(total_regions, 50) / 50)
                else:
                    avg_score = 0
                    total_regions = 0
                    combined_score = 0

            except Exception as e:
                logging.warning(f"OCR failed for angle {angle}: {e}")
                avg_score = 0
                total_regions = 0
                combined_score = 0

            results[angle] = {"avg_confidence": avg_score, "total_regions": total_regions, "combined_score": combined_score}
            if angle == 0:
                score_0 = combined_score

            logging.debug(f"Table orientation {angle}°: avg_conf={avg_score:.4f}, regions={total_regions}, combined={combined_score:.4f}")

            if combined_score > best_score:
                best_score = combined_score
                best_angle = angle
                best_img = rotated_img

        # Absolute threshold rule:
        # Only choose non-0° if it exceeds 0° by more than 0.2 and 0° score is below 0.8.
        if best_angle != 0 and score_0 is not None:
            if not (best_score - score_0 > 0.2 and score_0 < 0.8):
                best_angle = 0
                best_img = table_img
                best_score = score_0

        results[best_angle] = results.get(best_angle, {"avg_confidence": 0, "total_regions": 0, "combined_score": 0})

        logging.info(f"Best table orientation: {best_angle}° (score={best_score:.4f})")

        return best_angle, best_img, results
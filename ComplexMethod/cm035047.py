def generate_kernel(self, img_size, shrink_ratio, text_polys, ignore_tags=None):
        """
        Refer to part of the code:
        https://github.com/open-mmlab/mmocr/blob/main/mmocr/datasets/pipelines/textdet_targets/base_textdet_targets.py
        """

        h, w = img_size
        text_kernel = np.zeros((h, w), dtype=np.float32)
        for i, poly in enumerate(text_polys):
            polygon = Polygon(poly)
            distance = (
                polygon.area
                * (1 - shrink_ratio * shrink_ratio)
                / (polygon.length + 1e-6)
            )
            subject = [tuple(l) for l in poly]
            pco = pyclipper.PyclipperOffset()
            pco.AddPath(subject, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            shrunk = np.array(pco.Execute(-distance))

            if len(shrunk) == 0 or shrunk.size == 0:
                if ignore_tags is not None:
                    ignore_tags[i] = True
                continue
            try:
                shrunk = np.array(shrunk[0]).reshape(-1, 2)
            except:
                if ignore_tags is not None:
                    ignore_tags[i] = True
                continue
            cv2.fillPoly(text_kernel, [shrunk.astype(np.int32)], i + 1)
        return text_kernel, ignore_tags
def run(
        self,
        image_data,
        points_list,
        interpolation=None,
        ratio_width=1.0,
        ratio_height=1.0,
        loss_thresh=5.0,
        mode="calibration",
    ):
        if image_data is None:
            raise ValueError
        if not isinstance(points_list, list):
            raise ValueError
        for points in points_list:
            if not isinstance(points, list):
                raise ValueError
        if interpolation is None:
            interpolation = cv2.INTER_LINEAR

        if ratio_width < 1.0 or ratio_height < 1.0:
            raise ValueError(
                "ratio_width and ratio_height cannot be smaller than 1, but got {}",
                (ratio_width, ratio_height),
            )

        if mode.lower() != "calibration" and mode.lower() != "homography":
            raise ValueError(
                'mode must be ["calibration", "homography"], but got {}'.format(mode)
            )

        if mode.lower() == "homography" and ratio_width != 1.0 and ratio_height != 1.0:
            raise ValueError(
                "ratio_width and ratio_height must be 1.0 when mode is homography, but got mode:{}, ratio:({},{})".format(
                    mode, ratio_width, ratio_height
                )
            )

        res = []
        for points in points_list:
            rectified_img = self(
                image_data,
                points,
                interpolation,
                ratio_width,
                ratio_height,
                loss_thresh=loss_thresh,
                mode=mode,
            )
            res.append(rectified_img)

        visualized_image = self.visualize(image_data, points_list)

        return res, visualized_image
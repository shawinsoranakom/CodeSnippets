def predict(self, images=[], paths=[]):
        """
        Get the text angle in the predicted images.
        Args:
            images (list(numpy.ndarray)): images data, shape of each is [H, W, C]. If images not paths
            paths (list[str]): The paths of images. If paths not images
        Returns:
            res (list): The result of text detection box and save path of images.
        """

        if images != [] and isinstance(images, list) and paths == []:
            predicted_data = images
        elif images == [] and isinstance(paths, list) and paths != []:
            predicted_data = self.read_images(paths)
        else:
            raise TypeError("The input data is inconsistent with expectations.")

        assert (
            predicted_data != []
        ), "There is not any image to be predicted. Please check the input data."

        img_list = []
        for img in predicted_data:
            if img is None:
                continue
            img_list.append(img)

        rec_res_final = []
        try:
            img_list, cls_res, predict_time = self.text_classifier(img_list)
            for dno in range(len(cls_res)):
                angle, score = cls_res[dno]
                rec_res_final.append(
                    {
                        "angle": angle,
                        "confidence": float(score),
                    }
                )
        except Exception as e:
            print(e)
            return [[]]

        return [rec_res_final]
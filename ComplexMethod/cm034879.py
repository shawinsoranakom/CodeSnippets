def predict(self, images=[], paths=[]):
        """
        Get the chinese texts in the predicted images.
        Args:
            images (list(numpy.ndarray)): images data, shape of each is [H, W, C]. If images not paths
            paths (list[str]): The paths of images. If paths not images
        Returns:
            res (list): The result of chinese texts and save path of images.
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

        all_results = []
        for img in predicted_data:
            if img is None:
                logger.info("error in loading image")
                all_results.append([])
                continue
            starttime = time.time()
            dt_boxes, rec_res, _ = self.text_sys(img)
            elapse = time.time() - starttime
            logger.info("Predict time: {}".format(elapse))

            dt_num = len(dt_boxes)
            rec_res_final = []

            for dno in range(dt_num):
                text, score = rec_res[dno]
                rec_res_final.append(
                    {
                        "text": text,
                        "confidence": float(score),
                        "text_region": dt_boxes[dno].astype(np.int32).tolist(),
                    }
                )
            all_results.append(rec_res_final)
        return all_results
def predict(self, img_path: str, is_output_polygon=False, short_size: int = 1024):
        """
        对传入的图像进行预测，支持图像地址,opencv 读取图片，偏慢
        :param img_path: 图像地址
        :param is_numpy:
        :return:
        """
        assert os.path.exists(img_path), "file is not exists"
        img = cv2.imread(img_path, 1 if self.img_mode != "GRAY" else 0)
        if self.img_mode == "RGB":
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        img = resize_image(img, short_size)
        # 将图片由(w,h)变为(1,img_channel,h,w)
        tensor = self.transform(img)
        tensor = tensor.unsqueeze_(0)

        batch = {"shape": [(h, w)]}
        with paddle.no_grad():
            start = time.time()
            preds = self.model(tensor)
            box_list, score_list = self.post_process(
                batch, preds, is_output_polygon=is_output_polygon
            )
            box_list, score_list = box_list[0], score_list[0]
            if len(box_list) > 0:
                if is_output_polygon:
                    idx = [x.sum() > 0 for x in box_list]
                    box_list = [box_list[i] for i, v in enumerate(idx) if v]
                    score_list = [score_list[i] for i, v in enumerate(idx) if v]
                else:
                    idx = (
                        box_list.reshape(box_list.shape[0], -1).sum(axis=1) > 0
                    )  # 去掉全为0的框
                    box_list, score_list = box_list[idx], score_list[idx]
            else:
                box_list, score_list = [], []
            t = time.time() - start
        return preds[0, 0, :, :].detach().cpu().numpy(), box_list, score_list, t
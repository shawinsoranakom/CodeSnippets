def __call__(self, img_list):
        img_num = len(img_list)
        batch_num = self.sr_batch_num
        st = time.time()
        st = time.time()
        all_result = [] * img_num
        if self.benchmark:
            self.autolog.times.start()
        for beg_img_no in range(0, img_num, batch_num):
            end_img_no = min(img_num, beg_img_no + batch_num)
            norm_img_batch = []
            imgC, imgH, imgW = self.sr_image_shape
            for ino in range(beg_img_no, end_img_no):
                norm_img = self.resize_norm_img(img_list[ino])
                norm_img = norm_img[np.newaxis, :]
                norm_img_batch.append(norm_img)

            norm_img_batch = np.concatenate(norm_img_batch)
            norm_img_batch = norm_img_batch.copy()
            if self.benchmark:
                self.autolog.times.stamp()
            self.input_tensor.copy_from_cpu(norm_img_batch)
            self.predictor.run()
            outputs = []
            for output_tensor in self.output_tensors:
                output = output_tensor.copy_to_cpu()
                outputs.append(output)
            if len(outputs) != 1:
                preds = outputs
            else:
                preds = outputs[0]
            all_result.append(outputs)
        if self.benchmark:
            self.autolog.times.end(stamp=True)
        return all_result, time.time() - st
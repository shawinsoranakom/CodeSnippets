def __call__(self, img):
        ori_im = img.copy()
        data = {"image": img}
        data = transform(data, self.preprocess_op)
        if data[0] is None:
            return None, 0
        starttime = time.time()

        for idx in range(len(data)):
            if isinstance(data[idx], np.ndarray):
                data[idx] = np.expand_dims(data[idx], axis=0)
            else:
                data[idx] = [data[idx]]
        if self.args.use_onnx:
            input_tensor = {
                name: data[idx] for idx, name in enumerate(self.input_tensor)
            }
            self.output_tensors = self.predictor.run(None, input_tensor)
        else:
            for idx in range(len(self.input_tensor)):
                self.input_tensor[idx].copy_from_cpu(data[idx])

            self.predictor.run()

        outputs = []
        for output_tensor in self.output_tensors:
            output = (
                output_tensor if self.args.use_onnx else output_tensor.copy_to_cpu()
            )
            outputs.append(output)
        preds = outputs[0]

        post_result = self.postprocess_op(
            preds, segment_offset_ids=data[6], ocr_infos=data[7]
        )
        elapse = time.time() - starttime
        return post_result, data, elapse
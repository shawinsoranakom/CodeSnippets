def predict(self, img):
        ori_im = img.copy()
        data = {"image": img}

        st = time.time()

        if self.args.benchmark:
            self.autolog.times.start()

        data = transform(data, self.preprocess_op)
        img, shape_list = data
        if img is None:
            return None, 0
        img = np.expand_dims(img, axis=0)
        shape_list = np.expand_dims(shape_list, axis=0)
        img = img.copy()

        if self.args.benchmark:
            self.autolog.times.stamp()
        if self.use_onnx:
            input_dict = {}
            input_dict[self.input_tensor.name] = img
            outputs = self.predictor.run(self.output_tensors, input_dict)
        else:
            self.input_tensor.copy_from_cpu(img)
            self.predictor.run()
            outputs = []
            for output_tensor in self.output_tensors:
                output = output_tensor.copy_to_cpu()
                outputs.append(output)
            if self.args.benchmark:
                self.autolog.times.stamp()

        preds = {}
        if self.det_algorithm == "EAST":
            preds["f_geo"] = outputs[0]
            preds["f_score"] = outputs[1]
        elif self.det_algorithm == "SAST":
            preds["f_border"] = outputs[0]
            preds["f_score"] = outputs[1]
            preds["f_tco"] = outputs[2]
            preds["f_tvo"] = outputs[3]
        elif self.det_algorithm in ["DB", "PSE", "DB++"]:
            preds["maps"] = outputs[0]
        elif self.det_algorithm == "FCE":
            for i, output in enumerate(outputs):
                preds["level_{}".format(i)] = output
        elif self.det_algorithm == "CT":
            preds["maps"] = outputs[0]
            preds["score"] = outputs[1]
        else:
            raise NotImplementedError

        post_result = self.postprocess_op(preds, shape_list)
        dt_boxes = post_result[0]["points"]

        if self.args.det_box_type == "poly":
            dt_boxes = self.filter_tag_det_res_only_clip(dt_boxes, ori_im.shape)
        else:
            dt_boxes = self.filter_tag_det_res(dt_boxes, ori_im.shape)

        if self.args.benchmark:
            self.autolog.times.end(stamp=True)
        et = time.time()
        return dt_boxes, et - st
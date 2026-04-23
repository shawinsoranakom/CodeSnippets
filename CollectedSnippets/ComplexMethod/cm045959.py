def _batch_process_same_size(self, img_list):
        """
            对相同尺寸的图像进行批处理

            Args:
                img_list: 相同尺寸的图像列表

            Returns:
                batch_results: 批处理结果列表
                total_elapse: 总耗时
            """
        starttime = time.time()

        # 预处理所有图像
        batch_data = []
        batch_shapes = []
        ori_imgs = []

        for img in img_list:
            ori_im = img.copy()
            ori_imgs.append(ori_im)

            data = {'image': img}
            data = transform(data, self.preprocess_op)
            if data is None:
                # 如果预处理失败，返回空结果
                return [(None, 0) for _ in img_list], 0

            img_processed, shape_list = data
            batch_data.append(img_processed)
            batch_shapes.append(shape_list)

        # 堆叠成批处理张量
        try:
            batch_tensor = np.stack(batch_data, axis=0)
            batch_shapes = np.stack(batch_shapes, axis=0)
        except Exception as e:
            # 如果堆叠失败，回退到逐个处理
            batch_results = []
            for img in img_list:
                dt_boxes, elapse = self.__call__(img)
                batch_results.append((dt_boxes, elapse))
            return batch_results, time.time() - starttime

        # 批处理推理
        with torch.no_grad():
            inp = torch.from_numpy(batch_tensor)
            inp = inp.to(self.device)
            outputs = self.net(inp)

        # 处理输出
        preds = {}
        if self.det_algorithm == "EAST":
            preds['f_geo'] = outputs['f_geo'].cpu().numpy()
            preds['f_score'] = outputs['f_score'].cpu().numpy()
        elif self.det_algorithm == 'SAST':
            preds['f_border'] = outputs['f_border'].cpu().numpy()
            preds['f_score'] = outputs['f_score'].cpu().numpy()
            preds['f_tco'] = outputs['f_tco'].cpu().numpy()
            preds['f_tvo'] = outputs['f_tvo'].cpu().numpy()
        elif self.det_algorithm in ['DB', 'PSE', 'DB++']:
            preds['maps'] = outputs['maps'].cpu().numpy()
        elif self.det_algorithm == 'FCE':
            for i, (k, output) in enumerate(outputs.items()):
                preds['level_{}'.format(i)] = output.cpu().numpy()
        else:
            raise NotImplementedError

        # 后处理每个图像的结果
        batch_results = []
        total_elapse = time.time() - starttime

        for i in range(len(img_list)):
            # 提取单个图像的预测结果
            single_preds = {}
            for key, value in preds.items():
                if isinstance(value, np.ndarray):
                    single_preds[key] = value[i:i + 1]  # 保持批次维度
                else:
                    single_preds[key] = value

            # 后处理
            post_result = self.postprocess_op(single_preds, batch_shapes[i:i + 1])
            dt_boxes = post_result[0]['points']

            # 过滤和裁剪检测框
            dt_boxes = self._filter_det_res(dt_boxes, ori_imgs[i].shape)

            batch_results.append((dt_boxes, total_elapse / len(img_list)))

        return batch_results, total_elapse
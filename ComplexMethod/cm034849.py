def postprocess(self, x, shape_info, is_output_polygon):
        """postprocess
        Postprocess to the inference engine output.
        Args:
            x: Inference engine output.
        Returns: Output data after argmax.
        """
        box_list, score_list = self.post_process(
            shape_info, x, is_output_polygon=is_output_polygon
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
        return box_list, score_list
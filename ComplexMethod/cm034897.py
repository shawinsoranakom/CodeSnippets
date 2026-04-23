def accuracy(self, pred, target, topk=1, thresh=None):
        """Calculate accuracy according to the prediction and target.

        Args:
            pred (torch.Tensor): The model prediction, shape (N, num_class)
            target (torch.Tensor): The target of each prediction, shape (N, )
            topk (int | tuple[int], optional): If the predictions in ``topk``
                matches the target, the predictions will be regarded as
                correct ones. Defaults to 1.
            thresh (float, optional): If not None, predictions with scores under
                this threshold are considered incorrect. Default to None.

        Returns:
            float | tuple[float]: If the input ``topk`` is a single integer,
                the function will return a single float as accuracy. If
                ``topk`` is a tuple containing multiple integers, the
                function will return a tuple containing accuracies of
                each ``topk`` number.
        """
        assert isinstance(topk, (int, tuple))
        if isinstance(topk, int):
            topk = (topk,)
            return_single = True
        else:
            return_single = False

        maxk = max(topk)
        if pred.shape[0] == 0:
            accu = [pred.new_tensor(0.0) for i in range(len(topk))]
            return accu[0] if return_single else accu
        pred_value, pred_label = paddle.topk(pred, maxk, axis=1)
        pred_label = pred_label.transpose([1, 0])  # transpose to shape (maxk, N)
        correct = paddle.equal(
            pred_label, (target.reshape([1, -1]).expand_as(pred_label))
        )
        res = []
        for k in topk:
            correct_k = paddle.sum(
                correct[:k].reshape([-1]).astype("float32"), axis=0, keepdim=True
            )
            res.append(
                paddle.multiply(correct_k, paddle.to_tensor(100.0 / pred.shape[0]))
            )
        return res[0] if return_single else res
def forward(self, outputs, labels):
        predicts = outputs["maps"]
        predicts = F.interpolate(predicts, scale_factor=4)

        texts = predicts[:, 0, :, :]
        kernels = predicts[:, 1:, :, :]
        gt_texts, gt_kernels, training_masks = labels[1:]

        # text loss
        selected_masks = self.ohem_batch(texts, gt_texts, training_masks)

        loss_text = self.dice_loss(texts, gt_texts, selected_masks)
        iou_text = iou(
            (texts > 0).astype("int64"), gt_texts, training_masks, reduce=False
        )
        losses = dict(loss_text=loss_text, iou_text=iou_text)

        # kernel loss
        loss_kernels = []
        if self.kernel_sample_mask == "gt":
            selected_masks = gt_texts * training_masks
        elif self.kernel_sample_mask == "pred":
            selected_masks = (F.sigmoid(texts) > 0.5).astype("float32") * training_masks

        for i in range(kernels.shape[1]):
            kernel_i = kernels[:, i, :, :]
            gt_kernel_i = gt_kernels[:, i, :, :]
            loss_kernel_i = self.dice_loss(kernel_i, gt_kernel_i, selected_masks)
            loss_kernels.append(loss_kernel_i)
        loss_kernels = paddle.mean(paddle.stack(loss_kernels, axis=1), axis=1)
        iou_kernel = iou(
            (kernels[:, -1, :, :] > 0).astype("int64"),
            gt_kernels[:, -1, :, :],
            training_masks * gt_texts,
            reduce=False,
        )
        losses.update(dict(loss_kernels=loss_kernels, iou_kernel=iou_kernel))
        loss = self.alpha * loss_text + (1 - self.alpha) * loss_kernels
        losses["loss"] = loss
        if self.reduction == "sum":
            losses = {x: paddle.sum(v) for x, v in losses.items()}
        elif self.reduction == "mean":
            losses = {x: paddle.mean(v) for x, v in losses.items()}
        return losses
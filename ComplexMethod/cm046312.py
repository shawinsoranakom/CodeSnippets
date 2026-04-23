def forward(self, x):
        """Perform inference with NMS post-processing. Supports Detect, Segment, OBB and Pose.

        Args:
            x (torch.Tensor): The preprocessed tensor with shape (B, C, H, W).

        Returns:
            (torch.Tensor | tuple): Tensor of shape (B, max_det, 4 + 2 + extra_shape) where B is the batch size, or a
                tuple of (detections, proto) for segmentation models.
        """
        from functools import partial

        from torchvision.ops import nms

        preds = self.model(x)
        pred = preds[0] if isinstance(preds, tuple) else preds
        kwargs = dict(device=pred.device, dtype=pred.dtype)
        bs = pred.shape[0]
        pred = pred.transpose(-1, -2)  # shape(1,84,6300) to shape(1,6300,84)
        extra_shape = pred.shape[-1] - (4 + len(self.model.names))  # extras from Segment, OBB, Pose
        if self.args.dynamic and self.args.batch > 1:  # batch size needs to always be same due to loop unroll
            pad = torch.zeros(torch.max(torch.tensor(self.args.batch - bs), torch.tensor(0)), *pred.shape[1:], **kwargs)
            pred = torch.cat((pred, pad))
        boxes, scores, extras = pred.split([4, len(self.model.names), extra_shape], dim=2)
        scores, classes = scores.max(dim=-1)
        self.args.max_det = min(pred.shape[1], self.args.max_det)  # in case num_anchors < max_det
        # (N, max_det, 4 coords + 1 class score + 1 class label + extra_shape).
        out = torch.zeros(pred.shape[0], self.args.max_det, boxes.shape[-1] + 2 + extra_shape, **kwargs)
        for i in range(bs):
            box, cls, score, extra = boxes[i], classes[i], scores[i], extras[i]
            mask = score > self.args.conf
            if self.is_tf or (self.args.format == "onnx" and self.obb):
                # TFLite GatherND error if mask is empty
                score *= mask
                # Explicit length otherwise reshape error, hardcoded to `self.args.max_det * 5`
                mask = score.topk(min(self.args.max_det * 5, score.shape[0])).indices
            box, score, cls, extra = box[mask], score[mask], cls[mask], extra[mask]
            nmsbox = box.clone()
            # `8` is the minimum value experimented to get correct NMS results for obb
            multiplier = 8 if self.obb else 1 / max(len(self.model.names), 1)
            # Normalize boxes for NMS since large values for class offset causes issue with int8 quantization
            if self.args.format == "tflite":  # TFLite is already normalized
                nmsbox *= multiplier
            else:
                nmsbox = multiplier * (nmsbox / torch.tensor(x.shape[2:], **kwargs).max())
            if not self.args.agnostic_nms:  # class-wise NMS
                end = 2 if self.obb else 4
                # fully explicit expansion otherwise reshape error
                cls_offset = cls.view(cls.shape[0], 1).expand(cls.shape[0], end)
                offbox = nmsbox[:, :end] + cls_offset * multiplier
                nmsbox = torch.cat((offbox, nmsbox[:, end:]), dim=-1)
            nms_fn = (
                partial(
                    TorchNMS.fast_nms,
                    use_triu=not (
                        self.is_tf
                        or (self.args.opset or 14) < 14
                        or (self.args.format == "openvino" and self.args.int8)  # OpenVINO int8 error with triu
                    ),
                    iou_func=batch_probiou,
                    exit_early=False,
                )
                if self.obb
                else nms
            )
            keep = nms_fn(
                torch.cat([nmsbox, extra], dim=-1) if self.obb else nmsbox,
                score,
                self.args.iou,
            )[: self.args.max_det]
            dets = torch.cat(
                [box[keep], score[keep].view(-1, 1), cls[keep].view(-1, 1).to(out.dtype), extra[keep]], dim=-1
            )
            # Zero-pad to max_det size to avoid reshape error
            pad = (0, 0, 0, self.args.max_det - dets.shape[0])
            out[i] = torch.nn.functional.pad(dets, pad)
        return (out[:bs], preds[1]) if self.model.task == "segment" else out[:bs]
def forward_lrpc(self, x: list[torch.Tensor]) -> torch.Tensor | tuple:
        """Process features with fused text embeddings to generate detections for prompt-free model."""
        boxes, scores, index = [], [], []
        bs = x[0].shape[0]
        cv2 = self.cv2 if not self.end2end else self.one2one_cv2
        cv3 = self.cv3 if not self.end2end else self.one2one_cv3
        for i in range(self.nl):
            cls_feat = cv3[i](x[i])
            loc_feat = cv2[i](x[i])
            assert isinstance(self.lrpc[i], LRPCHead)
            box, score, idx = self.lrpc[i](
                cls_feat,
                loc_feat,
                0 if self.export and not self.dynamic else getattr(self, "conf", 0.001),
            )
            boxes.append(box.view(bs, self.reg_max * 4, -1))
            scores.append(score)
            index.append(idx)
        preds = dict(boxes=torch.cat(boxes, 2), scores=torch.cat(scores, 2), feats=x, index=torch.cat(index))
        y = self._inference(preds)
        if self.end2end:
            y = self.postprocess(y.permute(0, 2, 1))
        return y if self.export else (y, preds)
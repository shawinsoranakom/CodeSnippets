def _update_scores_and_boxes(
        self,
        out,
        hs,
        reference_boxes,
        prompt,
        prompt_mask,
        dec_presence_out=None,
        is_instance_prompt=False,
    ):
        """Update output dict with class scores and box predictions."""
        num_o2o = hs.size(2)
        # score prediction
        if self.use_dot_prod_scoring:
            dot_prod_scoring_head = self.dot_prod_scoring
            if is_instance_prompt and self.instance_dot_prod_scoring is not None:
                dot_prod_scoring_head = self.instance_dot_prod_scoring
            outputs_class = dot_prod_scoring_head(hs, prompt, prompt_mask)
        else:
            class_embed_head = self.class_embed
            if is_instance_prompt and self.instance_class_embed is not None:
                class_embed_head = self.instance_class_embed
            outputs_class = class_embed_head(hs)

        # box prediction
        box_head = self.transformer.decoder.bbox_embed
        if is_instance_prompt and self.transformer.decoder.instance_bbox_embed is not None:
            box_head = self.transformer.decoder.instance_bbox_embed
        anchor_box_offsets = box_head(hs)
        reference_boxes_inv_sig = inverse_sigmoid(reference_boxes)
        outputs_coord = (reference_boxes_inv_sig + anchor_box_offsets).sigmoid()
        outputs_boxes_xyxy = xywh2xyxy(outputs_coord)

        if dec_presence_out is not None:
            _update_out(out, "presence_logit_dec", dec_presence_out, update_aux=False)

        if self.supervise_joint_box_scores:
            assert dec_presence_out is not None
            prob_dec_presence_out = dec_presence_out.clone().sigmoid()
            if self.detach_presence_in_joint_score:
                prob_dec_presence_out = prob_dec_presence_out.detach()

            outputs_class = inverse_sigmoid(outputs_class.sigmoid() * prob_dec_presence_out.unsqueeze(2)).clamp(
                min=-10.0, max=10.0
            )

        _update_out(out, "pred_logits", outputs_class[:, :, :num_o2o], update_aux=False)
        _update_out(out, "pred_boxes", outputs_coord[:, :, :num_o2o], update_aux=False)
        _update_out(out, "pred_boxes_xyxy", outputs_boxes_xyxy[:, :, :num_o2o], update_aux=False)
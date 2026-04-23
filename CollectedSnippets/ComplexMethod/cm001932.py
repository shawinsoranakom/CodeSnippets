def prepare_config_and_inputs(self):
        output_attentions = self.output_attentions
        input_ids = ids_tensor([self.batch_size, self.seq_length], vocab_size=self.vocab_size)
        visual_feats = torch.rand(self.batch_size, self.num_visual_features, self.visual_feat_dim, device=torch_device)
        bounding_boxes = torch.rand(self.batch_size, self.num_visual_features, 4, device=torch_device)

        input_mask = None
        if self.use_lang_mask:
            input_mask = ids_tensor([self.batch_size, self.seq_length], vocab_size=2)
        token_type_ids = None
        if self.use_token_type_ids:
            token_type_ids = ids_tensor([self.batch_size, self.seq_length], self.type_vocab_size)
        obj_labels = None
        if self.task_obj_predict:
            obj_labels = {}
        if self.visual_attr_loss and self.task_obj_predict:
            obj_labels["attr"] = (
                ids_tensor([self.batch_size, self.num_visual_features], self.num_attr_labels),
                ids_tensor([self.batch_size, self.num_visual_features], self.num_attr_labels),
            )
        if self.visual_feat_loss and self.task_obj_predict:
            obj_labels["feat"] = (
                ids_tensor(
                    [self.batch_size, self.num_visual_features, self.visual_feat_dim], self.num_visual_features
                ),
                ids_tensor([self.batch_size, self.num_visual_features], self.num_visual_features),
            )
        if self.visual_obj_loss and self.task_obj_predict:
            obj_labels["obj"] = (
                ids_tensor([self.batch_size, self.num_visual_features], self.num_object_labels),
                ids_tensor([self.batch_size, self.num_visual_features], self.num_object_labels),
            )
        ans = None
        if self.task_qa:
            ans = ids_tensor([self.batch_size], self.num_qa_labels)
        masked_lm_labels = None
        if self.task_mask_lm:
            masked_lm_labels = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)
        matched_label = None
        if self.task_matched:
            matched_label = ids_tensor([self.batch_size], self.num_labels)

        config = self.get_config()

        return (
            config,
            input_ids,
            visual_feats,
            bounding_boxes,
            token_type_ids,
            input_mask,
            obj_labels,
            masked_lm_labels,
            matched_label,
            ans,
            output_attentions,
        )
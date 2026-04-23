def process_word_list_and_spans_to_inputs(self, sid, word_list, spans):
    """Constructs the fffner input with spans and types."""
    tokenized_word_list = self.tokenize_word_list(word_list)
    final_len = sum(len(x) for x in tokenized_word_list)
    final_len = 2 + 3 + 2 + 3 + final_len  # account for mask and brackets
    if final_len > self.max_len:
      print(f"final_len {final_len} too long, skipping")
      return
    for span_start, span_end, span_type, span_label in spans:
      assert span_type == "mask"
      input_ids = []
      input_ids.append(self.cls_token_id)
      for ids in tokenized_word_list[:span_start]:
        input_ids.extend(ids)

      if not self.ablation_span_type_together:
        if not self.ablation_no_brackets:
          input_ids.append(self.left_bracket)
        is_entity_token_pos = len(input_ids)
        input_ids.append(self.mask_id if not self.ablation_not_mask else 8487)
        if not self.ablation_no_brackets:
          input_ids.append(self.right_bracket)

      if not self.ablation_no_brackets:
        input_ids.append(self.left_bracket)
      for ids in tokenized_word_list[span_start:span_end + 1]:
        input_ids.extend(ids)
      if not self.ablation_no_brackets:
        input_ids.append(self.right_bracket)

      if not self.ablation_no_brackets:
        input_ids.append(self.left_bracket)

      entity_type_token_pos = len(input_ids)
      if self.ablation_span_type_together:
        is_entity_token_pos = len(input_ids)

      input_ids.append(self.mask_id if not self.ablation_not_mask else 2828)
      if not self.ablation_no_brackets:
        input_ids.append(self.right_bracket)

      for ids in tokenized_word_list[span_end + 1:]:
        input_ids.extend(ids)
      input_ids.append(self.sep_token_id)
      is_entity_label = span_label in self.label_to_entity_type_index
      entity_type_label = self.label_to_entity_type_index.get(span_label, 0)
      yield self.process_to_input(input_ids, is_entity_token_pos,
                                  entity_type_token_pos, is_entity_label,
                                  entity_type_label, sid, span_start, span_end)
def call(self, inputs: tf.Tensor,  # pytype: disable=annotation-type-mismatch
           image_info: Optional[tf.Tensor] = None,
           box_indices: Optional[tf.Tensor] = None,
           classes: Optional[tf.Tensor] = None,
           training: bool = None
           ) -> Dict[str, Optional[Any]]:
    batch_size = tf.shape(inputs)[0]
    backbone_features = self.backbone(inputs, training=training)

    if self.decoder:
      decoder_features = self.decoder(backbone_features)
      if self.mask_decoder:
        decoder_features2 = self.mask_decoder(backbone_features)
      else:
        decoder_features2 = decoder_features
    else:
      decoder_features = backbone_features

    level_class_heatmaps = self.class_head(decoder_features, training=training)
    level_dense_mask_embeddings = self.embedding_head(
        decoder_features, training=training)
    embedding_size = self.embedding_size

    class_heatmaps = []
    dense_mask_embeddings = []
    class_scoremaps = []
    for level in range(self.min_level, self.max_level + 1):
      if not training:
        class_scoremaps.append(
            tf.reshape(
                self.process_heatmap(level_class_heatmaps[level]),
                [batch_size, -1],
            )
        )
      class_heatmaps.append(
          tf.reshape(
              level_class_heatmaps[level], [batch_size, -1, self.num_classes]
          )
      )
      dense_mask_embeddings.append(
          tf.reshape(
              level_dense_mask_embeddings[level],
              [batch_size, -1, embedding_size],
          )
      )

    class_heatmaps = tf.concat(class_heatmaps, axis=1)
    dense_mask_embeddings = tf.concat(dense_mask_embeddings, axis=1)

    per_pixel_embeddings = self.per_pixel_embeddings_head(
        (backbone_features, decoder_features2), training=training
    )

    if not training:
      class_scoremaps = tf.concat(class_scoremaps, axis=1)
      confidence, top_indices = tf.nn.top_k(
          class_scoremaps, k=self.max_proposals
      )
      box_indices = top_indices // self.num_classes
      classes = top_indices % self.num_classes

    mask_embeddings = tf.gather(
        dense_mask_embeddings, box_indices, batch_dims=1
    )
    class_embeddings = tf.cast(
        self.class_embeddings(tf.maximum(classes, 0)), mask_embeddings.dtype
    )
    mask_embeddings_inputs = mask_embeddings + class_embeddings
    mask_embeddings = self.mlp(mask_embeddings_inputs)

    mask_proposal_logits = tf.einsum(
        'bqc,bhwc->bhwq', mask_embeddings, per_pixel_embeddings
    )
    mask_proposal_logits = tf.cast(mask_proposal_logits, tf.float32)

    if not training:
      outputs = {
          'classes': classes,
          'confidence': confidence,
          'mask_embeddings': mask_embeddings,
          'mask_proposal_logits': mask_proposal_logits,
          'class_heatmaps': class_heatmaps,
      }
      if self.panoptic_generator is not None:
        panoptic_outputs = self.panoptic_generator(
            outputs, images_info=image_info
        )
        outputs.update({'panoptic_outputs': panoptic_outputs})
      else:
        outputs['mask_proposal_logits'] = tf.image.resize(
            mask_proposal_logits, self.padded_output_size, 'bilinear'
        )
    else:
      outputs = {
          'class_heatmaps': class_heatmaps,
          'mask_proposal_logits': mask_proposal_logits,
          'mask_embeddings': mask_embeddings,
      }
    return outputs
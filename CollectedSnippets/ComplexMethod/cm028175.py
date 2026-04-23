def generate_training_data(vocab_ids, writer_lm_all, writer_seq_ae_all):
  """Generates training data."""

  # Construct training data writers
  writer_lm = build_shuffling_tf_record_writer(data.TRAIN_LM)
  writer_seq_ae = build_shuffling_tf_record_writer(data.TRAIN_SA)
  writer_class = build_shuffling_tf_record_writer(data.TRAIN_CLASS)
  writer_valid_class = build_tf_record_writer(data.VALID_CLASS)
  writer_rev_lm = build_shuffling_tf_record_writer(data.TRAIN_REV_LM)
  writer_bd_class = build_shuffling_tf_record_writer(data.TRAIN_BD_CLASS)
  writer_bd_valid_class = build_shuffling_tf_record_writer(data.VALID_BD_CLASS)

  for doc in document_generators.documents(
      dataset='train', include_unlabeled=True, include_validation=True):
    input_seq = build_input_sequence(doc, vocab_ids)
    if len(input_seq) < 2:
      continue
    rev_seq = data.build_reverse_sequence(input_seq)
    lm_seq = data.build_lm_sequence(input_seq)
    rev_lm_seq = data.build_lm_sequence(rev_seq)
    seq_ae_seq = data.build_seq_ae_sequence(input_seq)
    if doc.label is not None:
      # Used for sentiment classification.
      label_seq = data.build_labeled_sequence(
          input_seq,
          doc.label,
          label_gain=(FLAGS.label_gain and not doc.is_validation))
      bd_label_seq = data.build_labeled_sequence(
          data.build_bidirectional_seq(input_seq, rev_seq),
          doc.label,
          label_gain=(FLAGS.label_gain and not doc.is_validation))
      class_writer = writer_valid_class if doc.is_validation else writer_class
      bd_class_writer = (writer_bd_valid_class
                         if doc.is_validation else writer_bd_class)
      class_writer.write(label_seq.seq.SerializeToString())
      bd_class_writer.write(bd_label_seq.seq.SerializeToString())

    # Write
    lm_seq_ser = lm_seq.seq.SerializeToString()
    seq_ae_seq_ser = seq_ae_seq.seq.SerializeToString()
    writer_lm_all.write(lm_seq_ser)
    writer_seq_ae_all.write(seq_ae_seq_ser)
    if not doc.is_validation:
      writer_lm.write(lm_seq_ser)
      writer_rev_lm.write(rev_lm_seq.seq.SerializeToString())
      writer_seq_ae.write(seq_ae_seq_ser)

  # Close writers
  writer_lm.close()
  writer_seq_ae.close()
  writer_class.close()
  writer_valid_class.close()
  writer_rev_lm.close()
  writer_bd_class.close()
  writer_bd_valid_class.close()
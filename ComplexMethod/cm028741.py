def main(_):
  if FLAGS.tokenization == "WordPiece":
    if not FLAGS.vocab_file:
      raise ValueError(
          "FLAG vocab_file for word-piece tokenizer is not specified.")
  else:
    assert FLAGS.tokenization == "SentencePiece"
    if not FLAGS.sp_model_file:
      raise ValueError(
          "FLAG sp_model_file for sentence-piece tokenizer is not specified.")

  if FLAGS.fine_tuning_task_type != "retrieval":
    flags.mark_flag_as_required("train_data_output_path")

  if FLAGS.fine_tuning_task_type == "classification":
    input_meta_data = generate_classifier_dataset()
  elif FLAGS.fine_tuning_task_type == "regression":
    input_meta_data = generate_regression_dataset()
  elif FLAGS.fine_tuning_task_type == "retrieval":
    input_meta_data = generate_retrieval_dataset()
  elif FLAGS.fine_tuning_task_type == "squad":
    input_meta_data = generate_squad_dataset()
  else:
    assert FLAGS.fine_tuning_task_type == "tagging"
    input_meta_data = generate_tagging_dataset()

  tf.io.gfile.makedirs(os.path.dirname(FLAGS.meta_data_file_path))
  with tf.io.gfile.GFile(FLAGS.meta_data_file_path, "w") as writer:
    writer.write(json.dumps(input_meta_data, indent=4) + "\n")
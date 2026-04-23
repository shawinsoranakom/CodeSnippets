def generate_classifier_dataset():
  """Generates classifier dataset and returns input meta data."""
  if FLAGS.classification_task_name in [
      "COLA",
      "WNLI",
      "SST-2",
      "MRPC",
      "QQP",
      "STS-B",
      "MNLI",
      "QNLI",
      "RTE",
      "AX",
      "SUPERGLUE-RTE",
      "CB",
      "BoolQ",
      "WIC",
  ]:
    assert not FLAGS.input_data_dir or FLAGS.tfds_params
  else:
    assert (FLAGS.input_data_dir and FLAGS.classification_task_name or
            FLAGS.tfds_params)

  if FLAGS.tokenization == "WordPiece":
    tokenizer = tokenization.FullTokenizer(
        vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)
    processor_text_fn = tokenization.convert_to_unicode
  else:
    assert FLAGS.tokenization == "SentencePiece"
    tokenizer = tokenization.FullSentencePieceTokenizer(FLAGS.sp_model_file)
    processor_text_fn = functools.partial(
        tokenization.preprocess_text, lower=FLAGS.do_lower_case)

  if FLAGS.tfds_params:
    processor = classifier_data_lib.TfdsProcessor(
        tfds_params=FLAGS.tfds_params, process_text_fn=processor_text_fn)
    return classifier_data_lib.generate_tf_record_from_data_file(
        processor,
        None,
        tokenizer,
        train_data_output_path=FLAGS.train_data_output_path,
        eval_data_output_path=FLAGS.eval_data_output_path,
        test_data_output_path=FLAGS.test_data_output_path,
        max_seq_length=FLAGS.max_seq_length)
  else:
    processors = {
        "ax":
            classifier_data_lib.AxProcessor,
        "cola":
            classifier_data_lib.ColaProcessor,
        "imdb":
            classifier_data_lib.ImdbProcessor,
        "mnli":
            functools.partial(
                classifier_data_lib.MnliProcessor, mnli_type=FLAGS.mnli_type),
        "mrpc":
            classifier_data_lib.MrpcProcessor,
        "qnli":
            classifier_data_lib.QnliProcessor,
        "qqp":
            classifier_data_lib.QqpProcessor,
        "rte":
            classifier_data_lib.RteProcessor,
        "sst-2":
            classifier_data_lib.SstProcessor,
        "sts-b":
            classifier_data_lib.StsBProcessor,
        "xnli":
            functools.partial(
                classifier_data_lib.XnliProcessor,
                language=FLAGS.xnli_language),
        "paws-x":
            functools.partial(
                classifier_data_lib.PawsxProcessor,
                language=FLAGS.pawsx_language),
        "wnli":
            classifier_data_lib.WnliProcessor,
        "xtreme-xnli":
            functools.partial(
                classifier_data_lib.XtremeXnliProcessor,
                translated_data_dir=FLAGS.translated_input_data_dir,
                only_use_en_dev=FLAGS.only_use_en_dev),
        "xtreme-paws-x":
            functools.partial(
                classifier_data_lib.XtremePawsxProcessor,
                translated_data_dir=FLAGS.translated_input_data_dir,
                only_use_en_dev=FLAGS.only_use_en_dev),
        "ax-g":
            classifier_data_lib.AXgProcessor,
        "superglue-rte":
            classifier_data_lib.SuperGLUERTEProcessor,
        "cb":
            classifier_data_lib.CBProcessor,
        "boolq":
            classifier_data_lib.BoolQProcessor,
        "wic":
            classifier_data_lib.WnliProcessor,
    }
    task_name = FLAGS.classification_task_name.lower()
    if task_name not in processors:
      raise ValueError("Task not found: %s" % (task_name,))

    processor = processors[task_name](process_text_fn=processor_text_fn)
    return classifier_data_lib.generate_tf_record_from_data_file(
        processor,
        FLAGS.input_data_dir,
        tokenizer,
        train_data_output_path=FLAGS.train_data_output_path,
        eval_data_output_path=FLAGS.eval_data_output_path,
        test_data_output_path=FLAGS.test_data_output_path,
        max_seq_length=FLAGS.max_seq_length)
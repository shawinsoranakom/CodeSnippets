def generate_tf_record_from_data_file(processor,
                                      data_dir,
                                      tokenizer,
                                      train_data_output_path=None,
                                      eval_data_output_path=None,
                                      test_data_output_path=None,
                                      max_seq_length=128):
  """Generates and saves training data into a tf record file.

  Args:
      processor: Input processor object to be used for generating data. Subclass
        of `DataProcessor`.
      data_dir: Directory that contains train/eval/test data to process.
      tokenizer: The tokenizer to be applied on the data.
      train_data_output_path: Output to which processed tf record for training
        will be saved.
      eval_data_output_path: Output to which processed tf record for evaluation
        will be saved.
      test_data_output_path: Output to which processed tf record for testing
        will be saved. Must be a pattern template with {} if processor has
        language specific test data.
      max_seq_length: Maximum sequence length of the to be generated
        training/eval data.

  Returns:
      A dictionary containing input meta data.
  """
  assert train_data_output_path or eval_data_output_path

  label_list = processor.get_labels()
  label_type = getattr(processor, "label_type", None)
  is_regression = getattr(processor, "is_regression", False)
  has_sample_weights = getattr(processor, "weight_key", False)

  num_training_data = 0
  if train_data_output_path:
    train_input_data_examples = processor.get_train_examples(data_dir)
    file_based_convert_examples_to_features(train_input_data_examples,
                                            label_list, max_seq_length,
                                            tokenizer, train_data_output_path,
                                            label_type,
                                            processor.featurize_example)
    num_training_data = len(train_input_data_examples)

  if eval_data_output_path:
    eval_input_data_examples = processor.get_dev_examples(data_dir)
    file_based_convert_examples_to_features(eval_input_data_examples,
                                            label_list, max_seq_length,
                                            tokenizer, eval_data_output_path,
                                            label_type,
                                            processor.featurize_example)

  meta_data = {
      "processor_type": processor.get_processor_name(),
      "train_data_size": num_training_data,
      "max_seq_length": max_seq_length,
  }

  if test_data_output_path:
    test_input_data_examples = processor.get_test_examples(data_dir)
    if isinstance(test_input_data_examples, dict):
      for language, examples in test_input_data_examples.items():
        file_based_convert_examples_to_features(
            examples, label_list, max_seq_length, tokenizer,
            test_data_output_path.format(language), label_type,
            processor.featurize_example)
        meta_data["test_{}_data_size".format(language)] = len(examples)
    else:
      file_based_convert_examples_to_features(test_input_data_examples,
                                              label_list, max_seq_length,
                                              tokenizer, test_data_output_path,
                                              label_type,
                                              processor.featurize_example)
      meta_data["test_data_size"] = len(test_input_data_examples)

  if is_regression:
    meta_data["task_type"] = "bert_regression"
    meta_data["label_type"] = {int: "int", float: "float"}[label_type]
  else:
    meta_data["task_type"] = "bert_classification"
    meta_data["num_labels"] = len(processor.get_labels())
  if has_sample_weights:
    meta_data["has_sample_weights"] = True

  if eval_data_output_path:
    meta_data["eval_data_size"] = len(eval_input_data_examples)

  return meta_data
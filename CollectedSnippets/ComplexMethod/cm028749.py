def file_based_convert_examples_to_features(examples,
                                            label_list,
                                            max_seq_length,
                                            tokenizer,
                                            output_file,
                                            label_type=None,
                                            featurize_fn=None):
  """Convert a set of `InputExample`s to a TFRecord file."""

  tf.io.gfile.makedirs(os.path.dirname(output_file))
  writer = tf.io.TFRecordWriter(output_file)

  for ex_index, example in enumerate(examples):
    if ex_index % 10000 == 0:
      logging.info("Writing example %d of %d", ex_index, len(examples))

    if featurize_fn:
      feature = featurize_fn(ex_index, example, label_list, max_seq_length,
                             tokenizer)
    else:
      feature = convert_single_example(ex_index, example, label_list,
                                       max_seq_length, tokenizer)

    def create_int_feature(values):
      f = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
      return f

    def create_float_feature(values):
      f = tf.train.Feature(float_list=tf.train.FloatList(value=list(values)))
      return f

    features = collections.OrderedDict()
    features["input_ids"] = create_int_feature(feature.input_ids)
    features["input_mask"] = create_int_feature(feature.input_mask)
    features["segment_ids"] = create_int_feature(feature.segment_ids)
    if label_type is not None and label_type == float:
      features["label_ids"] = create_float_feature([feature.label_id])
    elif feature.label_id is not None:
      features["label_ids"] = create_int_feature([feature.label_id])
    features["is_real_example"] = create_int_feature(
        [int(feature.is_real_example)])
    if feature.weight is not None:
      features["weight"] = create_float_feature([feature.weight])
    if feature.example_id is not None:
      features["example_id"] = create_int_feature([feature.example_id])
    else:
      features["example_id"] = create_int_feature([ex_index])

    tf_example = tf.train.Example(features=tf.train.Features(feature=features))
    writer.write(tf_example.SerializeToString())
  writer.close()
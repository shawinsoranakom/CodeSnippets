def main(_):
  if not FLAGS.output_file:
    raise ValueError('You must supply the path to save to with --output_file')
  if FLAGS.is_video_model and not FLAGS.num_frames:
    raise ValueError(
        'Number of frames must be specified for video models with --num_frames')
  tf.logging.set_verbosity(tf.logging.INFO)
  with tf.Graph().as_default() as graph:
    dataset = dataset_factory.get_dataset(FLAGS.dataset_name, 'train',
                                          FLAGS.dataset_dir)
    network_fn = nets_factory.get_network_fn(
        FLAGS.model_name,
        num_classes=(dataset.num_classes - FLAGS.labels_offset),
        is_training=FLAGS.is_training)
    image_size = FLAGS.image_size or network_fn.default_image_size
    num_channels = 1 if FLAGS.use_grayscale else 3
    if FLAGS.is_video_model:
      input_shape = [
          FLAGS.batch_size, FLAGS.num_frames, image_size, image_size,
          num_channels
      ]
    else:
      input_shape = [FLAGS.batch_size, image_size, image_size, num_channels]
    placeholder = tf.placeholder(name='input', dtype=tf.float32,
                                 shape=input_shape)
    network_fn(placeholder)

    if FLAGS.quantize:
      contrib_quantize.create_eval_graph()

    graph_def = graph.as_graph_def()
    if FLAGS.write_text_graphdef:
      tf.io.write_graph(
          graph_def,
          os.path.dirname(FLAGS.output_file),
          os.path.basename(FLAGS.output_file),
          as_text=True)
    else:
      with gfile.GFile(FLAGS.output_file, 'wb') as f:
        f.write(graph_def.SerializeToString())
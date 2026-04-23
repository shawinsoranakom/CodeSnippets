def _run_inference():
  """Runs all images through depth model and saves depth maps."""
  ckpt_basename = os.path.basename(FLAGS.model_ckpt)
  ckpt_modelname = os.path.basename(os.path.dirname(FLAGS.model_ckpt))
  output_dir = os.path.join(FLAGS.output_dir,
                            FLAGS.kitti_video.replace('/', '_') + '_' +
                            ckpt_modelname + '_' + ckpt_basename)
  if not gfile.Exists(output_dir):
    gfile.MakeDirs(output_dir)
  inference_model = model.Model(is_training=False,
                                seq_length=FLAGS.seq_length,
                                batch_size=FLAGS.batch_size,
                                img_height=FLAGS.img_height,
                                img_width=FLAGS.img_width)
  vars_to_restore = util.get_vars_to_restore(FLAGS.model_ckpt)
  saver = tf.train.Saver(vars_to_restore)
  sv = tf.train.Supervisor(logdir='/tmp/', saver=None)
  with sv.managed_session() as sess:
    saver.restore(sess, FLAGS.model_ckpt)
    if FLAGS.kitti_video == 'test_files_eigen':
      im_files = util.read_text_lines(
          util.get_resource_path('dataset/kitti/test_files_eigen.txt'))
      im_files = [os.path.join(FLAGS.kitti_dir, f) for f in im_files]
    else:
      video_path = os.path.join(FLAGS.kitti_dir, FLAGS.kitti_video)
      im_files = gfile.Glob(os.path.join(video_path, 'image_02/data', '*.png'))
      im_files = [f for f in im_files if 'disp' not in f]
      im_files = sorted(im_files)
    for i in range(0, len(im_files), FLAGS.batch_size):
      if i % 100 == 0:
        logging.info('Generating from %s: %d/%d', ckpt_basename, i,
                     len(im_files))
      inputs = np.zeros(
          (FLAGS.batch_size, FLAGS.img_height, FLAGS.img_width, 3),
          dtype=np.uint8)
      for b in range(FLAGS.batch_size):
        idx = i + b
        if idx >= len(im_files):
          break
        im = scipy.misc.imread(im_files[idx])
        inputs[b] = scipy.misc.imresize(im, (FLAGS.img_height, FLAGS.img_width))
      results = inference_model.inference(inputs, sess, mode='depth')
      for b in range(FLAGS.batch_size):
        idx = i + b
        if idx >= len(im_files):
          break
        if FLAGS.kitti_video == 'test_files_eigen':
          depth_path = os.path.join(output_dir, '%03d.png' % idx)
        else:
          depth_path = os.path.join(output_dir, '%04d.png' % idx)
        depth_map = results['depth'][b]
        depth_map = np.squeeze(depth_map)
        colored_map = _normalize_depth_for_display(depth_map, cmap=CMAP)
        input_float = inputs[b].astype(np.float32) / 255.0
        vertical_stack = np.concatenate((input_float, colored_map), axis=0)
        scipy.misc.imsave(depth_path, vertical_stack)
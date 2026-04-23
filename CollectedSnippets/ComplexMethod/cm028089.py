def main(argv):
  if len(argv) > 1:
    raise RuntimeError('Too many command-line arguments.')

  # Read list of images.
  print('Reading list of images...')
  image_paths = _ReadImageList(cmd_args.list_images_path)
  num_images = len(image_paths)
  print(f'done! Found {num_images} images')

  # Create output directories if necessary.
  if not tf.io.gfile.exists(cmd_args.output_dir):
    tf.io.gfile.makedirs(cmd_args.output_dir)
  if cmd_args.output_viz_dir and not tf.io.gfile.exists(
      cmd_args.output_viz_dir):
    tf.io.gfile.makedirs(cmd_args.output_viz_dir)

  detector_fn = detector.MakeDetector(cmd_args.detector_path)

  start = time.time()
  for i, image_path in enumerate(image_paths):
    # Report progress once in a while.
    if i == 0:
      print('Starting to detect objects in images...')
    elif i % _STATUS_CHECK_ITERATIONS == 0:
      elapsed = (time.time() - start)
      print(f'Processing image {i} out of {num_images}, last '
            f'{_STATUS_CHECK_ITERATIONS} images took {elapsed} seconds')
      start = time.time()

    # If descriptor already exists, skip its computation.
    base_boxes_filename, _ = os.path.splitext(os.path.basename(image_path))
    out_boxes_filename = base_boxes_filename + _BOX_EXT
    out_boxes_fullpath = os.path.join(cmd_args.output_dir, out_boxes_filename)
    if tf.io.gfile.exists(out_boxes_fullpath):
      print(f'Skipping {image_path}')
      continue

    im = np.expand_dims(np.array(utils.RgbLoader(image_paths[i])), 0)

    # Extract and save boxes.
    (boxes_out, scores_out, class_indices_out) = detector_fn(im)
    (selected_boxes, selected_scores,
     selected_class_indices) = _FilterBoxesByScore(boxes_out[0], scores_out[0],
                                                   class_indices_out[0],
                                                   cmd_args.detector_thresh)

    box_io.WriteToFile(out_boxes_fullpath, selected_boxes, selected_scores,
                       selected_class_indices)
    if cmd_args.output_viz_dir:
      out_viz_filename = base_boxes_filename + _VIZ_SUFFIX
      out_viz_fullpath = os.path.join(cmd_args.output_viz_dir, out_viz_filename)
      _PlotBoxesAndSaveImage(im[0], selected_boxes, out_viz_fullpath)
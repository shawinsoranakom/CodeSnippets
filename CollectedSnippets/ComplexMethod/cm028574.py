def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  # Get list of images
  img_lists = []
  img_lists.extend(_IMG_FILE.value)
  for img_dir in _IMG_DIR.value:
    img_lists.extend(tf.io.gfile.glob(os.path.join(img_dir, '*')))

  logging.info('Total number of input images: %d', len(img_lists))

  model = load_model()

  vis_dis = _VIS_DIR.value

  output = {'annotations': []}
  for img_file in tqdm.tqdm(img_lists):
    output['annotations'].append({
        'image_id': img_file.split('/')[-1].split('.')[0],
        'paragraphs': inference(img_file, model),
    })

    if vis_dis:
      key = output['annotations'][-1]['image_id']
      paragraphs = output['annotations'][-1]['paragraphs']
      img = cv2.cvtColor(cv2.imread(img_file), cv2.COLOR_BGR2RGB)
      word_bnds = []
      line_bnds = []
      para_bnds = []
      for paragraph in paragraphs:
        paragraph_points_list = []
        for line in paragraph['lines']:
          line_points_list = []
          for word in line['words']:
            word_bnds.append(
                np.array(word['vertices'], np.int32).reshape((-1, 1, 2)))
            line_points_list.extend(word['vertices'])
          paragraph_points_list.extend(line_points_list)

          line_points = np.array(line_points_list, np.int32)  # (N,2)
          left = int(np.min(line_points[:, 0]))
          top = int(np.min(line_points[:, 1]))
          right = int(np.max(line_points[:, 0]))
          bottom = int(np.max(line_points[:, 1]))
          line_bnds.append(
              np.array([[[left, top]], [[right, top]], [[right, bottom]],
                        [[left, bottom]]], np.int32))
        para_points = np.array(paragraph_points_list, np.int32)  # (N,2)
        left = int(np.min(para_points[:, 0]))
        top = int(np.min(para_points[:, 1]))
        right = int(np.max(para_points[:, 0]))
        bottom = int(np.max(para_points[:, 1]))
        para_bnds.append(
            np.array([[[left, top]], [[right, top]], [[right, bottom]],
                      [[left, bottom]]], np.int32))

      for name, bnds in zip(['paragraph', 'line', 'word'],
                            [para_bnds, line_bnds, word_bnds]):
        vis = cv2.polylines(img, bnds, True, (0, 0, 255), 2)
        cv2.imwrite(os.path.join(vis_dis, f'{key}-{name}.jpg'),
                    cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))

  with tf.io.gfile.GFile(_OUTPUT_PATH.value, mode='w') as f:
    f.write(json.dumps(output, ensure_ascii=False, indent=2))
def main(unused_argv):
  workdir = FLAGS.workdir

  # Filter novel class annotations from the training and validation sets.
  for name in ('trainvalno5k', '5k'):
    file_path = os.path.join(workdir, 'datasplit', '{}.json'.format(name))
    with tf.io.gfile.GFile(file_path, 'r') as f:
      json_dict = json.load(f)

    json_dict['annotations'] = [a for a in json_dict['annotations']
                                if a['category_id'] in BASE_CLASS_IDS]
    output_path = os.path.join(
        workdir, 'datasplit', '{}_base.json'.format(name))
    with tf.io.gfile.GFile(output_path, 'w') as f:
      json.dump(json_dict, f)

  for seed, shots in itertools.product(SEEDS, SHOTS):
    # Retrieve all examples for a given seed and shots setting.
    file_paths = [os.path.join(workdir, suffix)
                  for suffix in FILE_SUFFIXES[(seed, shots)]]
    json_dicts = []
    for file_path in file_paths:
      with tf.io.gfile.GFile(file_path, 'r') as f:
        json_dicts.append(json.load(f))

    # Make sure that all JSON files for a given seed and shots setting have the
    # same metadata. We count on this to fuse them later on.
    metadata_dicts = [{'info': d['info'], 'licenses': d['licenses'],
                       'categories': d['categories']} for d in json_dicts]
    if not all(d == metadata_dicts[0] for d in metadata_dicts[1:]):
      raise RuntimeError(
          'JSON files for {} shots (seed {}) '.format(shots, seed) +
          'have different info, licences, or categories fields')

    # Retrieve images across all JSON files.
    images = sum((d['images'] for d in json_dicts), [])
    # Remove duplicate image entries.
    images = list({image['id']: image for image in images}.values())

    output_dict = {
        'info': json_dicts[0]['info'],
        'licenses': json_dicts[0]['licenses'],
        'categories': json_dicts[0]['categories'],
        'images': images,
        'annotations': sum((d['annotations'] for d in json_dicts), [])
    }

    output_path = os.path.join(workdir,
                               '{}shot_seed{}.json'.format(shots, seed))
    with tf.io.gfile.GFile(output_path, 'w') as f:
      json.dump(output_dict, f)
    logger.info('Processed %d shots (seed %d) and saved to %s',
                shots, seed, output_path)
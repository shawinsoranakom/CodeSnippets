def _get_clean_train_image_files_and_labels(csv_path, image_dir):
  """Get image file paths, image ids and  labels for the clean training split.

  Args:
    csv_path: path to the Google-landmark Dataset v2 CSV Data Sources files
              of the clean train dataset. Assumes CSV header landmark_id;images.
    image_dir: directory that stores downloaded images.

  Returns:
    image_paths: the paths to all images in the image_dir.
    file_ids: the unique ids of images.
    labels: the landmark id of all images.
    relabeling: relabeling rules created to replace actual labels with
                a continuous set of labels.
  """
  # Load the content of the CSV file (landmark_id/label -> images).
  with tf.io.gfile.GFile(csv_path, 'rb') as csv_file:
    df = pd.read_csv(csv_file)

  # Create the dictionary (key = image_id, value = {label, file_id}).
  images = {}
  for _, row in df.iterrows():
    label = row['landmark_id']
    for file_id in row['images'].split(' '):
      images[file_id] = {}
      images[file_id]['label'] = label
      images[file_id]['file_id'] = file_id

  # Add the full image path to the dictionary of images.
  image_paths = tf.io.gfile.glob(os.path.join(image_dir, '*.jpg'))
  for image_path in image_paths:
    file_id = os.path.basename(os.path.normpath(image_path))[:-4]
    if file_id in images:
      images[file_id]['image_path'] = image_path

  # Explode the dictionary into lists (1 per image attribute).
  image_paths = []
  file_ids = []
  labels = []
  for _, value in images.items():
    image_paths.append(value['image_path'])
    file_ids.append(value['file_id'])
    labels.append(value['label'])

  # Relabel image labels to contiguous values.
  unique_labels = sorted(set(labels))
  relabeling = {label: index for index, label in enumerate(unique_labels)}
  new_labels = [relabeling[label] for label in labels]
  return image_paths, file_ids, new_labels, relabeling
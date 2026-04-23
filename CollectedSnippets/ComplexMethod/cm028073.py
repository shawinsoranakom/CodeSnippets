def ReadSolution(file_path, task):
  """Reads solution from file, for a given task.

  Args:
    file_path: Path to CSV file with solution. File contains a header.
    task: Type of challenge task. Supported values: 'recognition', 'retrieval'.

  Returns:
    public_solution: Dict mapping test image ID to list of ground-truth IDs, for
      the Public subset of test images. If `task` == 'recognition', the IDs are
      integers corresponding to landmark IDs. If `task` == 'retrieval', the IDs
      are strings corresponding to index image IDs.
    private_solution: Same as `public_solution`, but for the private subset of
      test images.
    ignored_ids: List of test images that are ignored in scoring.

  Raises:
    ValueError: If Usage field is not Public, Private or Ignored; or if `task`
      is not supported.
  """
  public_solution = {}
  private_solution = {}
  ignored_ids = []
  with tf.io.gfile.GFile(file_path, 'r') as csv_file:
    reader = csv.reader(csv_file)
    next(reader, None)  # Skip header.
    for row in reader:
      test_id = row[0]
      if row[2] == 'Ignored':
        ignored_ids.append(test_id)
      else:
        ground_truth_ids = []
        if task == RECOGNITION_TASK_ID:
          if row[1]:
            for landmark_id in row[1].split(' '):
              ground_truth_ids.append(int(landmark_id))
        elif task == RETRIEVAL_TASK_ID:
          for image_id in row[1].split(' '):
            ground_truth_ids.append(image_id)
        else:
          raise ValueError('Unrecognized task: %s' % task)

        if row[2] == 'Public':
          public_solution[test_id] = ground_truth_ids
        elif row[2] == 'Private':
          private_solution[test_id] = ground_truth_ids
        else:
          raise ValueError('Test image %s has unrecognized Usage tag %s' %
                           (row[0], row[2]))

  return public_solution, private_solution, ignored_ids
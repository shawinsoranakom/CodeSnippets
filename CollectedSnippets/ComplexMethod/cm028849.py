def convert_groundtruths_to_coco_dataset(groundtruths, label_map=None):
  """Converts ground-truths to the dataset in COCO format.

  Args:
    groundtruths: a dictionary of numpy arrays including the fields below.
      Note that each element in the list represent the number for a single
      example without batch dimension. 'K' below denotes the actual number of
      instances for each image.
      Required fields:
        - source_id: a list of numpy arrays of int or string of shape
          [batch_size].
        - height: a list of numpy arrays of int of shape [batch_size].
        - width: a list of numpy arrays of int of shape [batch_size].
        - num_detections: a list of numpy arrays of int of shape [batch_size].
        - boxes: a list of numpy arrays of float of shape [batch_size, K, 4],
            where coordinates are in the original image space (not the
            normalized coordinates).
        - classes: a list of numpy arrays of int of shape [batch_size, K].
      Optional fields:
        - is_crowds: a list of numpy arrays of int of shape [batch_size, K]. If
            th field is absent, it is assumed that this instance is not crowd.
        - areas: a list of numy arrays of float of shape [batch_size, K]. If the
            field is absent, the area is calculated using either boxes or
            masks depending on which one is available.
        - masks: a list of numpy arrays of string of shape [batch_size, K],
    label_map: (optional) a dictionary that defines items from the category id
      to the category name. If `None`, collect the category mapping from the
      `groundtruths`.

  Returns:
    coco_groundtruths: the ground-truth dataset in COCO format.
  """
  source_ids = np.concatenate(groundtruths['source_id'], axis=0).reshape(-1)
  heights = np.concatenate(groundtruths['height'], axis=0).reshape(-1)
  widths = np.concatenate(groundtruths['width'], axis=0).reshape(-1)
  gt_images = [{'id': int(i), 'height': int(h), 'width': int(w)} for i, h, w
               in zip(source_ids, heights, widths)]

  gt_annotations = []
  num_batches = len(groundtruths['source_id'])
  for i in range(num_batches):
    logging.log_every_n(
        logging.INFO,
        'convert_groundtruths_to_coco_dataset: Processing annotation %d', 100,
        i)
    max_num_instances = groundtruths['classes'][i].shape[1]
    batch_size = groundtruths['source_id'][i].shape[0]
    for j in range(batch_size):
      num_instances = groundtruths['num_detections'][i][j]
      if num_instances > max_num_instances:
        logging.warning(
            'num_groundtruths is larger than max_num_instances, %d v.s. %d',
            num_instances, max_num_instances)
        num_instances = max_num_instances
      for k in range(int(np.squeeze(num_instances))):
        ann = {}
        ann['image_id'] = int(groundtruths['source_id'][i][j])
        if 'is_crowds' in groundtruths:
          ann['iscrowd'] = int(groundtruths['is_crowds'][i][j, k])
        else:
          ann['iscrowd'] = 0
        ann['category_id'] = int(groundtruths['classes'][i][j, k])
        boxes = groundtruths['boxes'][i]
        ann['bbox'] = [
            float(boxes[j, k, 1]),
            float(boxes[j, k, 0]),
            float(boxes[j, k, 3] - boxes[j, k, 1]),
            float(boxes[j, k, 2] - boxes[j, k, 0])]
        if 'areas' in groundtruths:
          ann['area'] = float(groundtruths['areas'][i][j, k])
        else:
          ann['area'] = float(
              (boxes[j, k, 3] - boxes[j, k, 1]) *
              (boxes[j, k, 2] - boxes[j, k, 0]))
        if 'masks' in groundtruths:
          if isinstance(groundtruths['masks'][i][j, k], tf.Tensor):
            mask = Image.open(
                six.BytesIO(groundtruths['masks'][i][j, k].numpy()))
          else:
            mask = Image.open(
                six.BytesIO(groundtruths['masks'][i][j, k]))
          np_mask = np.array(mask, dtype=np.uint8)
          np_mask[np_mask > 0] = 255
          encoded_mask = mask_api.encode(np.asfortranarray(np_mask))
          ann['segmentation'] = encoded_mask
          # Ensure the content of `counts` is JSON serializable string.
          if 'counts' in ann['segmentation']:
            ann['segmentation']['counts'] = six.ensure_str(
                ann['segmentation']['counts'])
          if 'areas' not in groundtruths:
            ann['area'] = mask_api.area(encoded_mask)
        if 'keypoints' in groundtruths:
          keypoints = groundtruths['keypoints'][i]
          coco_keypoints = []
          num_valid_keypoints = 0
          for z in range(len(keypoints[j, k, :, 1])):
            # Convert from [y, x] to [x, y] as mandated by COCO.
            x = float(keypoints[j, k, z, 1])
            y = float(keypoints[j, k, z, 0])
            coco_keypoints.append(x)
            coco_keypoints.append(y)
            if tf.math.is_nan(x) or tf.math.is_nan(y) or (
                x == 0 and y == 0):
              visibility = 0
            else:
              visibility = 2
              num_valid_keypoints = num_valid_keypoints + 1
            coco_keypoints.append(visibility)
          ann['keypoints'] = coco_keypoints
          ann['num_keypoints'] = num_valid_keypoints
        gt_annotations.append(ann)

  for i, ann in enumerate(gt_annotations):
    ann['id'] = i + 1

  if label_map:
    gt_categories = [{'id': i, 'name': label_map[i]} for i in label_map]
  else:
    category_ids = [gt['category_id'] for gt in gt_annotations]
    gt_categories = [{'id': i} for i in set(category_ids)]

  gt_dataset = {
      'images': gt_images,
      'categories': gt_categories,
      'annotations': copy.deepcopy(gt_annotations),
  }
  return gt_dataset
def coco_annotations_to_lists(bbox_annotations, id_to_name_map,
                              image_height, image_width, include_masks):
  """Converts COCO annotations to feature lists."""

  data = dict((k, list()) for k in
              ['xmin', 'xmax', 'ymin', 'ymax', 'is_crowd',
               'category_id', 'category_names', 'area'])
  if include_masks:
    data['encoded_mask_png'] = []

  num_annotations_skipped = 0

  for object_annotations in bbox_annotations:
    (x, y, width, height) = tuple(object_annotations['bbox'])

    if width <= 0 or height <= 0:
      num_annotations_skipped += 1
      continue
    if x + width > image_width or y + height > image_height:
      num_annotations_skipped += 1
      continue
    data['xmin'].append(float(x) / image_width)
    data['xmax'].append(float(x + width) / image_width)
    data['ymin'].append(float(y) / image_height)
    data['ymax'].append(float(y + height) / image_height)
    data['is_crowd'].append(object_annotations['iscrowd'])
    category_id = int(object_annotations['category_id'])
    data['category_id'].append(category_id)
    data['category_names'].append(id_to_name_map[category_id].encode('utf8'))
    data['area'].append(object_annotations['area'])

    if include_masks:
      data['encoded_mask_png'].append(
          coco_segmentation_to_mask_png(object_annotations['segmentation'],
                                        image_height, image_width,
                                        object_annotations['iscrowd'])
      )

  return data, num_annotations_skipped
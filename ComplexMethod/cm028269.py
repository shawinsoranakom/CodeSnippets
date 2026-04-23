def LoadAnnotations(self, annotations):
    """Load annotations dictionary into COCO datastructure.

    See http://mscoco.org/dataset/#format for a description of the annotations
    format.  As above, this function replicates the default behavior of the API
    but does not require writing to external storage.

    Args:
      annotations: python list holding object detection results where each
        detection is encoded as a dict with required keys ['image_id',
        'category_id', 'score'] and one of ['bbox', 'segmentation'] based on
        `detection_type`.

    Returns:
      a coco.COCO datastructure holding object detection annotations results

    Raises:
      ValueError: if annotations is not a list
      ValueError: if annotations do not correspond to the images contained
        in self.
    """
    results = coco.COCO()
    results.dataset['images'] = [img for img in self.dataset['images']]

    tf.logging.info('Loading and preparing annotation results...')
    tic = time.time()

    if not isinstance(annotations, list):
      raise ValueError('annotations is not a list of objects')
    annotation_img_ids = [ann['image_id'] for ann in annotations]
    if (set(annotation_img_ids) != (set(annotation_img_ids)
                                    & set(self.getImgIds()))):
      raise ValueError('Results do not correspond to current coco set')
    results.dataset['categories'] = copy.deepcopy(self.dataset['categories'])
    if self._detection_type == 'bbox':
      for idx, ann in enumerate(annotations):
        bb = ann['bbox']
        ann['area'] = bb[2] * bb[3]
        ann['id'] = idx + 1
        ann['iscrowd'] = 0
    elif self._detection_type == 'segmentation':
      for idx, ann in enumerate(annotations):
        ann['area'] = mask.area(ann['segmentation'])
        ann['bbox'] = mask.toBbox(ann['segmentation'])
        ann['id'] = idx + 1
        ann['iscrowd'] = 0
    tf.logging.info('DONE (t=%0.2fs)', (time.time() - tic))

    results.dataset['annotations'] = annotations
    results.createIndex()
    return results
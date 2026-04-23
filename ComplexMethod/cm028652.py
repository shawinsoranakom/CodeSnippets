def __call__(self,
               dataset,
               k,
               anchors_per_scale=None,
               scaling_mode="sqrt_log",
               box_generation_mode="across_level",
               image_resolution=(512, 512, 3),
               num_samples=-1):
    """Run k-means on th eboxes for a given input resolution.

    Args:
      dataset: `tf.data.Dataset` for the decoded object detection dataset. The
        boxes must have the key 'groundtruth_boxes'.
      k: `int` for the number for centroids to generate.
      anchors_per_scale: `int` for how many anchor boxes to use per level.
      scaling_mode: `str` for the type of box scaling to used when generating
        anchor boxes. Must be in the set {sqrt, default}.
      box_generation_mode: `str` for the type of kmeans to use when generating
        anchor boxes. Must be in the set {across_level, per_level}.
      image_resolution: `List[int]` for the resolution of the boxes to run
        k-means for.
      num_samples: `int` for number of samples to process in the dataset.

    Returns:
      boxes: `List[List[int]]` of shape [k, 2] for the anchor boxes to use for
        box predicitons.
    """
    self.get_box_from_dataset(dataset, num_samples=num_samples)

    if scaling_mode == "sqrt":
      boxes_ls = tf.math.sqrt(self._boxes.numpy())
    else:
      boxes_ls = self._boxes.numpy()

    if isinstance(image_resolution, int):
      image_resolution = [image_resolution, image_resolution]
    else:
      image_resolution = image_resolution[:2]
      image_resolution = image_resolution[::-1]

    if box_generation_mode == "even_split":
      clusters = self.get_init_centroids(boxes_ls, k)
      dists = 1 - self.iou(boxes_ls, np.array(clusters))
      assignments = tf.math.argmin(dists, axis=-1)
    elif box_generation_mode == "across_level":
      clusters = self.get_init_centroids(boxes_ls, k)
      clusters, assignments = self.run_kmeans(k, boxes_ls, clusters)
    else:
      # generate a box region for each FPN level
      clusters = self.get_init_centroids(boxes_ls, k//anchors_per_scale)

      # square off the clusters
      clusters += np.roll(clusters, 1, axis=-1)
      clusters /= 2

      # for each contained box set, compute K means
      boxes_sets = self.get_boxes(boxes_ls, clusters)
      clusters = []
      for boxes in boxes_sets:
        cluster_set, assignments = self.run_kmeans(anchors_per_scale, boxes)
        clusters.extend(cluster_set)
      clusters = np.array(clusters)

      dists = 1 - self.iou(boxes_ls, np.array(clusters))
      assignments = tf.math.argmin(dists, axis=-1)

    if scaling_mode == "sqrt":
      clusters = tf.square(clusters)

    self._boxes *= tf.convert_to_tensor(image_resolution, self._boxes.dtype)
    clusters = self.maximization(self._boxes, clusters, assignments)
    if hasattr(clusters, "numpy"):
      clusters = clusters.numpy()
    _, _, _ = self.avg_iou_total(self._boxes, clusters)
    clusters = np.floor(np.array(sorted(clusters, key=lambda x: x[0] * x[1])))
    return clusters.tolist()
def test_random_scale_crop_and_pad_to_square(self, scale):

    def graph_fn():
      image = np.random.randn(512, 256, 1)
      box_centers = [0.25, 0.5, 0.75]
      box_size = 0.1
      box_corners = []
      box_labels = []
      box_label_weights = []
      keypoints = []
      masks = []
      for center_y in box_centers:
        for center_x in box_centers:
          box_corners.append(
              [center_y - box_size / 2.0, center_x - box_size / 2.0,
               center_y + box_size / 2.0, center_x + box_size / 2.0])
          box_labels.append([1])
          box_label_weights.append([1.])
          keypoints.append(
              [[center_y - box_size / 2.0, center_x - box_size / 2.0],
               [center_y + box_size / 2.0, center_x + box_size / 2.0]])
          masks.append(image[:, :, 0].reshape(512, 256))

      image = tf.constant(image)
      boxes = tf.constant(box_corners)
      labels = tf.constant(box_labels)
      label_weights = tf.constant(box_label_weights)
      keypoints = tf.constant(keypoints)
      masks = tf.constant(np.stack(masks))

      (new_image, new_boxes, _, _, new_masks,
       new_keypoints) = preprocessor.random_scale_crop_and_pad_to_square(
           image,
           boxes,
           labels,
           label_weights,
           masks=masks,
           keypoints=keypoints,
           scale_min=scale,
           scale_max=scale,
           output_size=512)
      return new_image, new_boxes, new_masks, new_keypoints

    image, boxes, masks, keypoints = self.execute_cpu(graph_fn, [])

    # Since random_scale_crop_and_pad_to_square may prune and clip boxes,
    # we only need to find one of the boxes that was not clipped and check
    # that it matches the expected dimensions. Note, assertAlmostEqual(a, b)
    # is equivalent to round(a-b, 7) == 0.
    any_box_has_correct_size = False
    effective_scale_y = int(scale * 512) / 512.0
    effective_scale_x = int(scale * 256) / 512.0
    expected_size_y = 0.1 * effective_scale_y
    expected_size_x = 0.1 * effective_scale_x
    for box in boxes:
      ymin, xmin, ymax, xmax = box
      any_box_has_correct_size |= (
          (round(ymin, 7) != 0.0) and (round(xmin, 7) != 0.0) and
          (round(ymax, 7) != 1.0) and (round(xmax, 7) != 1.0) and
          (round((ymax - ymin) - expected_size_y, 7) == 0.0) and
          (round((xmax - xmin) - expected_size_x, 7) == 0.0))
    self.assertTrue(any_box_has_correct_size)

    # Similar to the approach above where we check for at least one box with the
    # expected dimensions, we check for at least one pair of keypoints whose
    # distance matches the expected dimensions.
    any_keypoint_pair_has_correct_dist = False
    for keypoint_pair in keypoints:
      ymin, xmin = keypoint_pair[0]
      ymax, xmax = keypoint_pair[1]
      any_keypoint_pair_has_correct_dist |= (
          (round(ymin, 7) != 0.0) and (round(xmin, 7) != 0.0) and
          (round(ymax, 7) != 1.0) and (round(xmax, 7) != 1.0) and
          (round((ymax - ymin) - expected_size_y, 7) == 0.0) and
          (round((xmax - xmin) - expected_size_x, 7) == 0.0))
    self.assertTrue(any_keypoint_pair_has_correct_dist)

    self.assertAlmostEqual(512.0, image.shape[0])
    self.assertAlmostEqual(512.0, image.shape[1])

    self.assertAllClose(image[:, :, 0],
                        masks[0, :, :])
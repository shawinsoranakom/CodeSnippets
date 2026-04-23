def build_loss(self):
    """Adds ops for computing loss."""
    with tf.name_scope('compute_loss'):
      self.reconstr_loss = 0
      self.smooth_loss = 0
      self.ssim_loss = 0
      self.icp_transform_loss = 0
      self.icp_residual_loss = 0

      # self.images is organized by ...[scale][B, h, w, seq_len * 3].
      self.images = [{} for _ in range(NUM_SCALES)]
      # Following nested lists are organized by ...[scale][source-target].
      self.warped_image = [{} for _ in range(NUM_SCALES)]
      self.warp_mask = [{} for _ in range(NUM_SCALES)]
      self.warp_error = [{} for _ in range(NUM_SCALES)]
      self.ssim_error = [{} for _ in range(NUM_SCALES)]
      self.icp_transform = [{} for _ in range(NUM_SCALES)]
      self.icp_residual = [{} for _ in range(NUM_SCALES)]

      self.middle_frame_index = util.get_seq_middle(self.seq_length)

      # Compute losses at each scale.
      for s in range(NUM_SCALES):
        # Scale image stack.
        height_s = int(self.img_height / (2**s))
        width_s = int(self.img_width / (2**s))
        self.images[s] = tf.image.resize_area(self.image_stack,
                                              [height_s, width_s])

        # Smoothness.
        if self.smooth_weight > 0:
          for i in range(self.seq_length):
            # In legacy mode, use the depth map from the middle frame only.
            if not self.legacy_mode or i == self.middle_frame_index:
              self.smooth_loss += 1.0 / (2**s) * self.depth_smoothness(
                  self.disp[i][s], self.images[s][:, :, :, 3 * i:3 * (i + 1)])

        for i in range(self.seq_length):
          for j in range(self.seq_length):
            # Only consider adjacent frames.
            if i == j or abs(i - j) != 1:
              continue
            # In legacy mode, only consider the middle frame as target.
            if self.legacy_mode and j != self.middle_frame_index:
              continue
            source = self.images[s][:, :, :, 3 * i:3 * (i + 1)]
            target = self.images[s][:, :, :, 3 * j:3 * (j + 1)]
            target_depth = self.depth[j][s]
            key = '%d-%d' % (i, j)

            # Extract ego-motion from i to j
            egomotion_index = min(i, j)
            egomotion_mult = 1
            if i > j:
              # Need to inverse egomotion when going back in sequence.
              egomotion_mult *= -1
            # For compatiblity with SfMLearner, interpret all egomotion vectors
            # as pointing toward the middle frame.  Note that unlike SfMLearner,
            # each vector captures the motion to/from its next frame, and not
            # the center frame.  Although with seq_length == 3, there is no
            # difference.
            if self.legacy_mode:
              if egomotion_index >= self.middle_frame_index:
                egomotion_mult *= -1
            egomotion = egomotion_mult * self.egomotion[:, egomotion_index, :]

            # Inverse warp the source image to the target image frame for
            # photometric consistency loss.
            self.warped_image[s][key], self.warp_mask[s][key] = (
                project.inverse_warp(source,
                                     target_depth,
                                     egomotion,
                                     self.intrinsic_mat[:, s, :, :],
                                     self.intrinsic_mat_inv[:, s, :, :]))

            # Reconstruction loss.
            self.warp_error[s][key] = tf.abs(self.warped_image[s][key] - target)
            self.reconstr_loss += tf.reduce_mean(
                self.warp_error[s][key] * self.warp_mask[s][key])
            # SSIM.
            if self.ssim_weight > 0:
              self.ssim_error[s][key] = self.ssim(self.warped_image[s][key],
                                                  target)
              # TODO(rezama): This should be min_pool2d().
              ssim_mask = slim.avg_pool2d(self.warp_mask[s][key], 3, 1, 'VALID')
              self.ssim_loss += tf.reduce_mean(
                  self.ssim_error[s][key] * ssim_mask)
            # 3D loss.
            if self.icp_weight > 0:
              cloud_a = self.cloud[j][s]
              cloud_b = self.cloud[i][s]
              self.icp_transform[s][key], self.icp_residual[s][key] = icp(
                  cloud_a, egomotion, cloud_b)
              self.icp_transform_loss += 1.0 / (2**s) * tf.reduce_mean(
                  tf.abs(self.icp_transform[s][key]))
              self.icp_residual_loss += 1.0 / (2**s) * tf.reduce_mean(
                  tf.abs(self.icp_residual[s][key]))

      self.total_loss = self.reconstr_weight * self.reconstr_loss
      if self.smooth_weight > 0:
        self.total_loss += self.smooth_weight * self.smooth_loss
      if self.ssim_weight > 0:
        self.total_loss += self.ssim_weight * self.ssim_loss
      if self.icp_weight > 0:
        self.total_loss += self.icp_weight * (self.icp_transform_loss +
                                              self.icp_residual_loss)
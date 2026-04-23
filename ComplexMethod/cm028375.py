def build_summaries(self):
    """Adds scalar and image summaries for TensorBoard."""
    tf.summary.scalar('total_loss', self.total_loss)
    tf.summary.scalar('reconstr_loss', self.reconstr_loss)
    if self.smooth_weight > 0:
      tf.summary.scalar('smooth_loss', self.smooth_loss)
    if self.ssim_weight > 0:
      tf.summary.scalar('ssim_loss', self.ssim_loss)
    if self.icp_weight > 0:
      tf.summary.scalar('icp_transform_loss', self.icp_transform_loss)
      tf.summary.scalar('icp_residual_loss', self.icp_residual_loss)

    for i in range(self.seq_length - 1):
      tf.summary.histogram('tx%d' % i, self.egomotion[:, i, 0])
      tf.summary.histogram('ty%d' % i, self.egomotion[:, i, 1])
      tf.summary.histogram('tz%d' % i, self.egomotion[:, i, 2])
      tf.summary.histogram('rx%d' % i, self.egomotion[:, i, 3])
      tf.summary.histogram('ry%d' % i, self.egomotion[:, i, 4])
      tf.summary.histogram('rz%d' % i, self.egomotion[:, i, 5])

    for s in range(NUM_SCALES):
      for i in range(self.seq_length):
        tf.summary.image('scale%d_image%d' % (s, i),
                         self.images[s][:, :, :, 3 * i:3 * (i + 1)])
        if i in self.depth:
          tf.summary.histogram('scale%d_depth%d' % (s, i), self.depth[i][s])
          tf.summary.histogram('scale%d_disp%d' % (s, i), self.disp[i][s])
          tf.summary.image('scale%d_disparity%d' % (s, i), self.disp[i][s])

      for key in self.warped_image[s]:
        tf.summary.image('scale%d_warped_image%s' % (s, key),
                         self.warped_image[s][key])
        tf.summary.image('scale%d_warp_mask%s' % (s, key),
                         self.warp_mask[s][key])
        tf.summary.image('scale%d_warp_error%s' % (s, key),
                         self.warp_error[s][key])
        if self.ssim_weight > 0:
          tf.summary.image('scale%d_ssim_error%s' % (s, key),
                           self.ssim_error[s][key])
        if self.icp_weight > 0:
          tf.summary.image('scale%d_icp_residual%s' % (s, key),
                           self.icp_residual[s][key])
          transform = self.icp_transform[s][key]
          tf.summary.histogram('scale%d_icp_tx%s' % (s, key), transform[:, 0])
          tf.summary.histogram('scale%d_icp_ty%s' % (s, key), transform[:, 1])
          tf.summary.histogram('scale%d_icp_tz%s' % (s, key), transform[:, 2])
          tf.summary.histogram('scale%d_icp_rx%s' % (s, key), transform[:, 3])
          tf.summary.histogram('scale%d_icp_ry%s' % (s, key), transform[:, 4])
          tf.summary.histogram('scale%d_icp_rz%s' % (s, key), transform[:, 5])
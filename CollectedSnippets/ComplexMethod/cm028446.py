def _summarize(ap=1, iou_thr=None, area_rng='all', max_dets=100):
      p = self.params
      i_str = (' {:<18} {} @[ IoU={:<9} | area={:>6s} | maxDets={:>3d} ] = '
               '{:0.3f}')
      title_str = 'Average Precision' if ap == 1 else 'Average Recall'
      type_str = '(AP)' if ap == 1 else '(AR)'
      iou_str = '{:0.2f}:{:0.2f}'.format(
          p.iouThrs[0],
          p.iouThrs[-1]) if iou_thr is None else '{:0.2f}'.format(iou_thr)

      aind = [i for i, a_rng in enumerate(p.areaRngLbl) if a_rng == area_rng]
      mind = [i for i, m_det in enumerate(p.maxDets) if m_det == max_dets]
      if ap == 1:
        # dimension of precision: [TxRxKxAxM]
        s = self.eval['precision']
        # IoU
        if iou_thr is not None:
          t = np.where(iou_thr == p.iouThrs)[0]
          s = s[t]
        s = s[:, :, :, aind, mind]
      else:
        # dimension of recall: [TxKxAxM]
        s = self.eval['recall']
        if iou_thr is not None:
          t = np.where(iou_thr == p.iouThrs)[0]
          s = s[t]
        s = s[:, :, aind, mind]

      if not (s[s > -1]).any():
        mean_s = -1
      else:
        mean_s = np.mean(s[s > -1])
        print(
            i_str.format(title_str, type_str, iou_str, area_rng, max_dets,
                         mean_s))
      return mean_s
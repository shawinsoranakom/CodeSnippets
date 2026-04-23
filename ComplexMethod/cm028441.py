def evaluateImg(self, img_id, cat_id, a_rng, max_det):
    p = self.params
    if p.useCats:
      gt = self._gts[img_id, cat_id]
      dt = self._dts[img_id, cat_id]
    else:
      gt, dt = [], []
      for c_id in p.catIds:
        gt.extend(self._gts[img_id, c_id])
        dt.extend(self._dts[img_id, c_id])

    if not gt and not dt:
      return None

    for g in gt:
      if g['ignore'] or (g['area'] < a_rng[0] or g['area'] > a_rng[1]):
        g['_ignore'] = 1
      else:
        g['_ignore'] = 0
      # Class manipulation: ignore the 'ignored_split'.
      if 'ignored_split' in g and g['ignored_split'] == 1:
        g['_ignore'] = 1

    # sort dt highest score first, sort gt ignore last
    gtind = np.argsort([g['_ignore'] for g in gt], kind='mergesort')
    gt = [gt[i] for i in gtind]
    dtind = np.argsort([-d['score'] for d in dt], kind='mergesort')
    dt = [dt[i] for i in dtind[0:max_det]]
    iscrowd = [int(o['iscrowd']) for o in gt]
    # load computed ious
    # ious = self.ious[img_id, cat_id][:, gtind] if len(
    #     self.ious[img_id, cat_id]) > 0 else self.ious[img_id, cat_id]
    if self.ious[img_id, cat_id].any():
      ious = self.ious[img_id, cat_id][:, gtind]
    else:
      ious = self.ious[img_id, cat_id]

    tt = len(p.iouThrs)
    gg = len(gt)
    dd = len(dt)
    gtm = np.zeros((tt, gg))
    dtm = np.zeros((tt, dd))
    gt_ig = np.array([g['_ignore'] for g in gt])
    dt_ig = np.zeros((tt, dd))
    # indicator of whether the gt object class is of ignored_split or not.
    gt_ig_split = np.array([g['ignored_split'] for g in gt])
    dt_ig_split = np.zeros((dd))

    if ious.any():
      for tind, t in enumerate(p.iouThrs):
        for dind, d in enumerate(dt):
          # information about best match so far (m=-1 -> unmatched)
          iou = min([t, 1 - 1e-10])
          m = -1
          for gind, g in enumerate(gt):
            # if this gt already matched, and not a crowd, continue
            if gtm[tind, gind] > 0 and not iscrowd[gind]:
              continue
            # if dt matched to reg gt, and on ignore gt, stop
            if m > -1 and gt_ig[m] == 0 and gt_ig[gind] == 1:
              break
            # continue to next gt unless better match made
            if ious[dind, gind] < iou:
              continue
            # if match successful and best so far, store appropriately
            iou = ious[dind, gind]
            m = gind
          # if match made store id of match for both dt and gt
          if m == -1:
            continue
          dt_ig[tind, dind] = gt_ig[m]
          dtm[tind, dind] = gt[m]['id']
          gtm[tind, m] = d['id']

          # Activate to ignore the seen-class detections.
          if tind == 0:  # Register just only once: tind > 0 is also fine.
            dt_ig_split[dind] = gt_ig_split[m]

    # set unmatched detections outside of area range to ignore
    a = np.array([d['area'] < a_rng[0] or d['area'] > a_rng[1] for d in dt
                 ]).reshape((1, len(dt)))
    dt_ig = np.logical_or(dt_ig, np.logical_and(dtm == 0, np.repeat(a, tt, 0)))

    # Activate to ignore the seen-class detections.
    # Take only eval_split (eg, nonvoc) and ignore seen_split (eg, voc).
    if dt_ig_split.sum() > 0:
      dtm = dtm[:, dt_ig_split == 0]
      dt_ig = dt_ig[:, dt_ig_split == 0]
      len_dt = min(max_det, len(dt))
      dt = [dt[i] for i in range(len_dt) if dt_ig_split[i] == 0]

    # store results for given image and category
    return {
        'image_id': img_id,
        'category_id': cat_id,
        'aRng': a_rng,
        'maxDet': max_det,
        'dtIds': [d['id'] for d in dt],
        'gtIds': [g['id'] for g in gt],
        'dtMatches': dtm,
        'gtMatches': gtm,
        'dtScores': [d['score'] for d in dt],
        'gtIgnore': gt_ig,
        'dtIgnore': dt_ig,
    }
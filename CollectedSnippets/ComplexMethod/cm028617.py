def evaluate(self) -> Mapping[str, Any]:
    """Compute the final metrics.

    Returns:
      metric_dict: A dict of metrics, contains following breakdown keys:
        mAP/{class}_level_1
        mAP/{class}_[0, 30)_level_1
        mAP/{class}_[30, 50)_level_1
        mAP/{class}_[50, +inf)_level_1
        mAP/{class}_level_2
        mAP/{class}_[0, 30)_level_2
        mAP/{class}_[30, 50)_level_2
        mAP/{class}_[50, +inf)_level_2
        mAPH/{class}_level_1
        mAPH/{class}_[0, 30)_level_1
        mAPH/{class}_[30, 50)_level_1
        mAPH/{class}_[50, +inf)_level_1
        mAPH/{class}_level_2
        mAPH/{class}_[0, 30)_level_2
        mAPH/{class}_[30, 50)_level_2
        mAPH/{class}_[50, +inf)_level_2
      It also contains following keys used as public NAS rewards.
        AP
        APH
    """
    ap, aph, _, _, _, _, _ = super().evaluate()
    metric_dict = {}
    for i, name in enumerate(self._breakdown_names):
      # Skip sign metrics since we don't use this type.
      if 'SIGN' in name:
        continue
      # Make metric name more readable.
      name = name.lower()
      for c in utils.CLASSES:
        pos = name.find(c)
        if pos != -1:
          name = name[pos:]
      if self._classes == 'all' or self._classes in name:
        metric_dict['mAP/{}'.format(name)] = ap[i]
        metric_dict['mAPH/{}'.format(name)] = aph[i]

    # Set public metrics as AP and APH.
    if self._classes == 'all':
      ap, aph = 0, 0
      for c in utils.CLASSES:
        ap += metric_dict['mAP/{}_level_1'.format(c)]
        aph += metric_dict['mAPH/{}_level_1'.format(c)]
      metric_dict['AP'] = ap / len(utils.CLASSES)
      metric_dict['APH'] = aph / len(utils.CLASSES)
    else:
      metric_dict['AP'] = metric_dict['mAP/{}_level_1'.format(self._classes)]
      metric_dict['APH'] = metric_dict['mAPH/{}_level_1'.format(self._classes)]
    return metric_dict
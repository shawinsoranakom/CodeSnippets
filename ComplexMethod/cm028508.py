def reduce_aggregated_logs(self, aggregated_logs, global_step=None):
    sentence_prediction_is_entity = np.concatenate(
        aggregated_logs['sentence_prediction_is_entity'], axis=0)
    sentence_prediction_is_entity = np.reshape(
        sentence_prediction_is_entity,
        (-1, self.task_config.model.num_classes_is_entity))
    sentence_prediction_entity_type = np.concatenate(
        aggregated_logs['sentence_prediction_entity_type'], axis=0)
    sentence_prediction_entity_type = np.reshape(
        sentence_prediction_entity_type,
        (-1, self.task_config.model.num_classes_entity_type))
    labels_is_entity = np.concatenate(
        aggregated_logs['labels_is_entity'], axis=0)
    labels_is_entity = np.reshape(labels_is_entity, -1)
    labels_entity_type = np.concatenate(
        aggregated_logs['labels_entity_type'], axis=0)
    labels_entity_type = np.reshape(labels_entity_type, -1)

    ids = np.concatenate(aggregated_logs['ids'], axis=0)
    ids = np.reshape(ids, -1)
    sentence_id = np.concatenate(aggregated_logs['sentence_id'], axis=0)
    sentence_id = np.reshape(sentence_id, -1)
    span_start = np.concatenate(aggregated_logs['span_start'], axis=0)
    span_start = np.reshape(span_start, -1)
    span_end = np.concatenate(aggregated_logs['span_end'], axis=0)
    span_end = np.reshape(span_end, -1)

    def resolve(length, spans, prediction_confidence):
      used = [False] * length
      spans = sorted(
          spans,
          key=lambda x: prediction_confidence[(x[0], x[1])],
          reverse=True)
      real_spans = []
      for span_start, span_end, ent_type in spans:
        fill = False
        for s in range(span_start, span_end + 1):
          if used[s]:
            fill = True
            break
        if not fill:
          real_spans.append((span_start, span_end, ent_type))
          for s in range(span_start, span_end + 1):
            used[s] = True
      return real_spans

    def get_p_r_f(truth, pred):
      n_pred = len(pred)
      n_truth = len(truth)
      n_correct = len(set(pred) & set(truth))
      precision = 1. * n_correct / n_pred if n_pred != 0 else 0.0
      recall = 1. * n_correct / n_truth if n_truth != 0 else 0.0
      f1 = 2 * precision * recall / (
          precision + recall) if precision + recall != 0.0 else 0.0
      return {
          'n_pred': n_pred,
          'n_truth': n_truth,
          'n_correct': n_correct,
          'precision': precision,
          'recall': recall,
          'f1': f1,
      }

    def softmax(x):
      x = np.array(x)
      e_x = np.exp(x - np.max(x))
      return e_x / e_x.sum(axis=0)

    per_sid_results = collections.defaultdict(list)
    for _, sent_id, sp_start, sp_end, is_entity_label, is_entity_logit, entity_type_label, entity_type_logit in zip(
        ids, sentence_id, span_start, span_end, labels_is_entity,
        sentence_prediction_is_entity, labels_entity_type,
        sentence_prediction_entity_type):
      if sent_id > 0:
        per_sid_results[sent_id].append(
            (sp_start, sp_end, is_entity_label, is_entity_logit,
             entity_type_label, entity_type_logit))
    ground_truth = []
    prediction_is_entity = []
    prediction_entity_type = []
    for key in sorted(list(per_sid_results.keys())):
      results = per_sid_results[key]
      gt_entities = []
      predictied_entities = []
      prediction_confidence = {}
      prediction_confidence_type = {}
      length = 0
      for span_start, span_end, ground_truth_span, prediction_span, ground_truth_type, prediction_type in results:
        if ground_truth_span == 1:
          gt_entities.append((span_start, span_end, ground_truth_type))
        if prediction_span[1] > prediction_span[0]:
          predictied_entities.append(
              (span_start, span_end, np.argmax(prediction_type).item()))
        prediction_confidence[(span_start,
                               span_end)] = max(softmax(prediction_span))
        prediction_confidence_type[(span_start,
                                    span_end)] = max(softmax(prediction_type))
        length = max(length, span_end)
      length += 1
      ground_truth.extend([(key, *x) for x in gt_entities])
      prediction_is_entity.extend([(key, *x) for x in predictied_entities])
      resolved_predicted = resolve(length, predictied_entities,
                                   prediction_confidence)
      prediction_entity_type.extend([(key, *x) for x in resolved_predicted])

    raw = get_p_r_f(ground_truth, prediction_is_entity)
    resolved = get_p_r_f(ground_truth, prediction_entity_type)
    return {
        'raw_f1': raw['f1'],
        'raw_precision': raw['precision'],
        'raw_recall': raw['recall'],
        'resolved_f1': resolved['f1'],
        'resolved_precision': resolved['precision'],
        'resolved_recall': resolved['recall'],
        'overall_f1': raw['f1'] + resolved['f1'],
    }
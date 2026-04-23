def aggregate_logs(self, state=None, step_outputs=None):
    if state is None:
      state = {
          'sentence_prediction_is_entity': [],
          'sentence_prediction_entity_type': [],
          'labels_is_entity': [],
          'labels_entity_type': [],
          'ids': [],
          'sentence_id': [],
          'span_start': [],
          'span_end': []
      }
    state['sentence_prediction_is_entity'].append(
        np.concatenate(
            [v.numpy() for v in step_outputs['sentence_prediction_is_entity']],
            axis=0))
    state['sentence_prediction_entity_type'].append(
        np.concatenate([
            v.numpy() for v in step_outputs['sentence_prediction_entity_type']
        ],
                       axis=0))
    state['labels_is_entity'].append(
        np.concatenate([v.numpy() for v in step_outputs['labels_is_entity']],
                       axis=0))
    state['labels_entity_type'].append(
        np.concatenate([v.numpy() for v in step_outputs['labels_entity_type']],
                       axis=0))
    state['ids'].append(
        np.concatenate([v.numpy() for v in step_outputs['id']], axis=0))
    state['sentence_id'].append(
        np.concatenate([v.numpy() for v in step_outputs['sentence_id']],
                       axis=0))
    state['span_start'].append(
        np.concatenate([v.numpy() for v in step_outputs['span_start']], axis=0))
    state['span_end'].append(
        np.concatenate([v.numpy() for v in step_outputs['span_end']], axis=0))
    return state
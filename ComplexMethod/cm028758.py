def _get_best_indexes_and_logits(result,
                                 n_best_size,
                                 xlnet_format=False):
  """Generates the n-best indexes and logits from a list."""
  if xlnet_format:
    for i in range(n_best_size):
      for j in range(n_best_size):
        j_index = i * n_best_size + j
        yield (result.start_indexes[i], result.start_logits[i],
               result.end_indexes[j_index], result.end_logits[j_index])
  else:
    start_index_and_score = sorted(enumerate(result.start_logits),
                                   key=lambda x: x[1], reverse=True)
    end_index_and_score = sorted(enumerate(result.end_logits),
                                 key=lambda x: x[1], reverse=True)
    for i in range(len(start_index_and_score)):
      if i >= n_best_size:
        break
      for j in range(len(end_index_and_score)):
        if j >= n_best_size:
          break
        yield (start_index_and_score[i][0], start_index_and_score[i][1],
               end_index_and_score[j][0], end_index_and_score[j][1])
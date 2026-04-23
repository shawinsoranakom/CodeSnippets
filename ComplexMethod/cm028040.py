def save_if_best_dev_model(self, sess, global_step):
    best_avg_score = 0
    for i, results in enumerate(self.history):
      if any("train" in metric for metric, value in results):
        continue
      total, count = 0, 0
      for metric, value in results:
        if "f1" in metric or "las" in metric or "accuracy" in metric:
          total += value
          count += 1
      avg_score = total / count
      if avg_score >= best_avg_score:
        best_avg_score = avg_score
        if i == len(self.history) - 1:
          utils.log("New best model! Saving...")
          self.best_model_saver.save(sess, self.config.best_model_checkpoint,
                                     global_step=global_step)
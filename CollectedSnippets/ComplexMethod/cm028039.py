def train(self, sess, progress, summary_writer):
    heading = lambda s: utils.heading(s, '(' + self._config.model_name + ')')
    trained_on_sentences = 0
    start_time = time.time()
    unsupervised_loss_total, unsupervised_loss_count = 0, 0
    supervised_loss_total, supervised_loss_count = 0, 0
    for mb in self._get_training_mbs(progress.unlabeled_data_reader):
      if mb.task_name != 'unlabeled':
        loss = self._model.train_labeled(sess, mb)
        supervised_loss_total += loss
        supervised_loss_count += 1

      if mb.task_name == 'unlabeled':
        self._model.run_teacher(sess, mb)
        loss = self._model.train_unlabeled(sess, mb)
        unsupervised_loss_total += loss
        unsupervised_loss_count += 1
        mb.teacher_predictions.clear()

      trained_on_sentences += mb.size
      global_step = self._model.get_global_step(sess)

      if global_step % self._config.print_every == 0:
        utils.log('step {:} - '
                  'supervised loss: {:.2f} - '
                  'unsupervised loss: {:.2f} - '
                  '{:.1f} sentences per second'.format(
            global_step,
            supervised_loss_total / max(1, supervised_loss_count),
            unsupervised_loss_total / max(1, unsupervised_loss_count),
            trained_on_sentences / (time.time() - start_time)))
        unsupervised_loss_total, unsupervised_loss_count = 0, 0
        supervised_loss_total, supervised_loss_count = 0, 0

      if global_step % self._config.eval_dev_every == 0:
        heading('EVAL ON DEV')
        self.evaluate_all_tasks(sess, summary_writer, progress.history)
        progress.save_if_best_dev_model(sess, global_step)
        utils.log()

      if global_step % self._config.eval_train_every == 0:
        heading('EVAL ON TRAIN')
        self.evaluate_all_tasks(sess, summary_writer, progress.history, True)
        utils.log()

      if global_step % self._config.save_model_every == 0:
        heading('CHECKPOINTING MODEL')
        progress.write(sess, global_step)
        utils.log()
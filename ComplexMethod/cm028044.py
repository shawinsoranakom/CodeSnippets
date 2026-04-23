def evaluate_checkpoint(checkpoint_path):
    """Performs a one-time evaluation of the given checkpoint.

    Args:
      checkpoint_path: Checkpoint to evaluate.
    Returns:
      True if the evaluation process should stop
    """
    restore_fn = tf.contrib.framework.assign_from_checkpoint_fn(
        checkpoint_path,
        uvf_utils.get_all_vars(),
        ignore_missing_vars=True,
        reshape_variables=False)
    assert restore_fn is not None, 'cannot restore %s' % checkpoint_path
    restore_fn(sess)
    global_step = sess.run(slim.get_global_step())
    should_stop = False
    max_reward = -1e10
    max_meta_reward = -1e10

    for eval_tag, (eval_step, env_base,) in sorted(eval_step_fns.items()):
      if hasattr(env_base, 'set_sess'):
        env_base.set_sess(sess)  # set session

      if generate_summaries:
        tf.logging.info(
            '[%s] Computing average reward over %d episodes at global step %d.',
            eval_tag, num_episodes_eval, global_step)
        (average_reward, last_reward,
         average_meta_reward, last_meta_reward, average_success,
         states, actions) = eval_utils.compute_average_reward(
             sess, env_base, eval_step, gamma, max_steps_per_episode,
             num_episodes_eval)
        tf.logging.info('[%s] Average reward = %f', eval_tag, average_reward)
        tf.logging.info('[%s] Last reward = %f', eval_tag, last_reward)
        tf.logging.info('[%s] Average meta reward = %f', eval_tag, average_meta_reward)
        tf.logging.info('[%s] Last meta reward = %f', eval_tag, last_meta_reward)
        tf.logging.info('[%s] Average success = %f', eval_tag, average_success)
        if model_rollout_fn is not None:
          preds, model_losses = eval_utils.compute_model_loss(
              sess, model_rollout_fn, states, actions)
          for i, (pred, state, model_loss) in enumerate(
              zip(preds, states, model_losses)):
            tf.logging.info('[%s] Model rollout step %d: loss=%f', eval_tag, i,
                            model_loss)
            tf.logging.info('[%s] Model rollout step %d: pred=%s', eval_tag, i,
                            str(pred.tolist()))
            tf.logging.info('[%s] Model rollout step %d: state=%s', eval_tag, i,
                            str(state.tolist()))

        # Report the eval stats to the tuner.
        if average_reward > max_reward:
          max_reward = average_reward
        if average_meta_reward > max_meta_reward:
          max_meta_reward = average_meta_reward

        for (tag, value) in [('Reward/average_%s_reward', average_reward),
                             ('Reward/last_%s_reward', last_reward),
                             ('Reward/average_%s_meta_reward', average_meta_reward),
                             ('Reward/last_%s_meta_reward', last_meta_reward),
                             ('Reward/average_%s_success', average_success)]:
          summary_str = tf.Summary(value=[
              tf.Summary.Value(
                  tag=tag % eval_tag,
                  simple_value=value)
          ])
          summary_writer.add_summary(summary_str, global_step)
          summary_writer.flush()

      if generate_videos or should_stop:
        # Do a manual reset before generating the video to see the initial
        # pose of the robot, towards which the reset controller is moving.
        if hasattr(env_base, '_gym_env'):
          tf.logging.info('Resetting before recording video')
          if hasattr(env_base._gym_env, 'reset_model'):
            env_base._gym_env.reset_model()  # pylint: disable=protected-access
          else:
            env_base._gym_env.wrapped_env.reset_model()
        video_filename = os.path.join(output_dir, 'videos',
                                      '%s_step_%d.mp4' % (eval_tag,
                                                          global_step))
        eval_utils.capture_video(sess, eval_step, env_base,
                                max_steps_per_episode * num_episodes_videos,
                                video_filename, video_settings,
                                reset_every=max_steps_per_episode)

      should_stop = should_stop or (generate_summaries and tuner_hook and
                                    tuner_hook(max_reward, global_step))
    return bool(should_stop)
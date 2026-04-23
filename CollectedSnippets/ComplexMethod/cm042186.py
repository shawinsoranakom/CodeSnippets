def get_msg(self, valid: bool, debug: bool = False) -> capnp._DynamicStructBuilder:
    msg = messaging.new_message('liveDelay')

    msg.valid = valid

    liveDelay = msg.liveDelay

    valid_mean_lag, valid_std, current_mean_lag, current_std = self.block_avg.get()
    if self.block_avg.valid_blocks >= self.min_valid_block_count and not np.isnan(valid_mean_lag) and not np.isnan(valid_std):
      if valid_std > MAX_LAG_STD:
        liveDelay.status = log.LiveDelayData.Status.invalid
      else:
        liveDelay.status = log.LiveDelayData.Status.estimated
    else:
      liveDelay.status = log.LiveDelayData.Status.unestimated

    if liveDelay.status == log.LiveDelayData.Status.estimated:
      liveDelay.lateralDelay = min(MAX_LAG, max(MIN_LAG, valid_mean_lag))
    else:
      liveDelay.lateralDelay = self.initial_lag

    if not np.isnan(current_mean_lag) and not np.isnan(current_std):
      liveDelay.lateralDelayEstimate = current_mean_lag
      liveDelay.lateralDelayEstimateStd = current_std
    else:
      liveDelay.lateralDelayEstimate = self.initial_lag
      liveDelay.lateralDelayEstimateStd = 0.0

    liveDelay.validBlocks = self.block_avg.valid_blocks
    liveDelay.calPerc = min(100 * (self.block_avg.valid_blocks * self.block_size + self.block_avg.idx) //
                            (self.min_valid_block_count * self.block_size), 100)
    if debug:
      liveDelay.points = self.block_avg.values.flatten().tolist()

    return msg
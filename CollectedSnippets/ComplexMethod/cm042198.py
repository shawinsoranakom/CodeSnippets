def test_estimator_basics(self, subtests):
    for lag_frames in range(3, 10):
      with subtests.test(msg=f"lag_frames={lag_frames}"):
        mocked_CP = car.CarParams(steerActuatorDelay=0.8)
        estimator = LateralLagEstimator(mocked_CP, DT, min_recovery_buffer_sec=0.0, min_yr=0.0)
        process_messages(estimator, lag_frames, int(MIN_OKAY_WINDOW_SEC / DT) + BLOCK_NUM_NEEDED * BLOCK_SIZE)
        msg = estimator.get_msg(True)
        assert msg.liveDelay.status == 'estimated'
        assert np.allclose(msg.liveDelay.lateralDelay, lag_frames * DT, atol=0.01)
        assert np.allclose(msg.liveDelay.lateralDelayEstimate, lag_frames * DT, atol=0.01)
        assert np.allclose(msg.liveDelay.lateralDelayEstimateStd, 0.0, atol=0.01)
        assert msg.liveDelay.validBlocks == BLOCK_NUM_NEEDED
        assert msg.liveDelay.calPerc == 100
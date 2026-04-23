def test_calibration_auto_reset(self):
    c = Calibrator(param_put=False)
    process_messages(c, [0.0, 0.0, 0.0], BLOCK_SIZE * INPUTS_NEEDED)
    assert c.valid_blocks == INPUTS_NEEDED
    np.testing.assert_allclose(c.rpy, [0.0, 0.0, 0.0], atol=1e-3)
    process_messages(c, [0.0, MAX_ALLOWED_PITCH_SPREAD*0.9, MAX_ALLOWED_YAW_SPREAD*0.9], BLOCK_SIZE + 10)
    assert c.valid_blocks == INPUTS_NEEDED + 1
    assert c.cal_status == log.LiveCalibrationData.Status.calibrated

    c = Calibrator(param_put=False)
    process_messages(c, [0.0, 0.0, 0.0], BLOCK_SIZE * INPUTS_NEEDED)
    assert c.valid_blocks == INPUTS_NEEDED
    np.testing.assert_allclose(c.rpy, [0.0, 0.0, 0.0])
    process_messages(c, [0.0, MAX_ALLOWED_PITCH_SPREAD*1.1, 0.0], BLOCK_SIZE + 10)
    assert c.valid_blocks == 1
    assert c.cal_status == log.LiveCalibrationData.Status.recalibrating
    np.testing.assert_allclose(c.rpy, [0.0, MAX_ALLOWED_PITCH_SPREAD*1.1, 0.0], atol=1e-2)

    c = Calibrator(param_put=False)
    process_messages(c, [0.0, 0.0, 0.0], BLOCK_SIZE * INPUTS_NEEDED)
    assert c.valid_blocks == INPUTS_NEEDED
    np.testing.assert_allclose(c.rpy, [0.0, 0.0, 0.0])
    process_messages(c, [0.0, 0.0, MAX_ALLOWED_YAW_SPREAD*1.1], BLOCK_SIZE + 10)
    assert c.valid_blocks == 1
    assert c.cal_status == log.LiveCalibrationData.Status.recalibrating
    np.testing.assert_allclose(c.rpy, [0.0, 0.0, MAX_ALLOWED_YAW_SPREAD*1.1], atol=1e-2)
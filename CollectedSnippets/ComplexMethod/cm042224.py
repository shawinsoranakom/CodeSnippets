def migrate_driverMonitoringState(msgs):
  ops = []
  for index, msg in msgs:
    old = msg.driverMonitoringStateDEPRECATED
    new_msg = messaging.new_message('driverMonitoringState', valid=msg.valid, logMonoTime=msg.logMonoTime)
    dm = new_msg.driverMonitoringState
    dm.isRHD = old.isRHD
    dm.activePolicy = log.DriverMonitoringState.MonitoringPolicy.vision if old.isActiveMode else \
                          log.DriverMonitoringState.MonitoringPolicy.wheeltouch

    AlertLevel = log.DriverMonitoringState.AlertLevel
    event_to_alert_level = {
      'driverDistracted1': AlertLevel.one, 'driverUnresponsive1': AlertLevel.one,
      'driverDistracted2': AlertLevel.two, 'driverUnresponsive2': AlertLevel.two,
      'driverDistracted3': AlertLevel.three, 'driverUnresponsive3': AlertLevel.three,
      'tooDistracted': AlertLevel.three,
    }
    for event in old.events:
      level = event_to_alert_level.get(str(event.name))
      if level is not None:
        dm.alertLevel = level
        break

    dm.visionPolicyState.awarenessPercent = int(max(0, min(100, (old.awarenessStatus if old.isActiveMode else old.awarenessActive) * 100)))
    dm.visionPolicyState.awarenessStep = old.stepChange if old.isActiveMode else 0.
    dm.visionPolicyState.isDistracted = old.isDistracted
    dm.visionPolicyState.faceDetected = old.faceDetected
    dm.visionPolicyState.pose.pitchCalib.offset = old.posePitchOffset
    dm.visionPolicyState.pose.pitchCalib.calibratedPercent = int(min(100, old.posePitchValidCount / 600 * 100))
    dm.visionPolicyState.pose.yawCalib.offset = old.poseYawOffset
    dm.visionPolicyState.pose.yawCalib.calibratedPercent = int(min(100, old.poseYawValidCount / 600 * 100))
    dm.visionPolicyState.pose.calibrated = old.posePitchValidCount >= 600 and old.poseYawValidCount >= 600
    dm.wheeltouchPolicyState.awarenessPercent = int(max(0, min(100, (old.awarenessPassive if old.isActiveMode else old.awarenessStatus) * 100)))
    dm.wheeltouchPolicyState.awarenessStep = 0. if old.isActiveMode else old.stepChange
    ops.append((index, new_msg.as_reader()))

  return ops, [], []
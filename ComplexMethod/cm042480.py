def main():
  params = Params()
  cloudlog.info("joystickd is waiting for CarParams")
  CP = messaging.log_from_bytes(params.get("CarParams", block=True), car.CarParams)

  sm = messaging.SubMaster(['carState', 'carControl', 'controlsState', 'selfdriveState', 'modelV2'], poll='modelV2')
  pm = messaging.PubMaster(['longitudinalPlan', 'driverAssistance', 'alertDebug'])

  maneuvers = iter(MANEUVERS)
  maneuver = None

  while True:
    sm.update()

    if maneuver is None:
      maneuver = next(maneuvers, None)

    alert_msg = messaging.new_message('alertDebug')
    alert_msg.valid = True

    plan_send = messaging.new_message('longitudinalPlan')
    plan_send.valid = sm.all_checks()

    longitudinalPlan = plan_send.longitudinalPlan
    accel = 0
    v_ego = max(sm['carState'].vEgo, 0)

    if maneuver is not None:
      accel = maneuver.get_accel(v_ego, sm['carControl'].longActive, sm['carState'].standstill, sm['carState'].cruiseState.standstill)

      if maneuver.active:
        alert_msg.alertDebug.alertText1 = f'Maneuver Active: {accel:0.2f} m/s^2'
      else:
        alert_msg.alertDebug.alertText1 = f'Setting up to {maneuver.initial_speed * CV.MS_TO_MPH:0.2f} mph'
      alert_msg.alertDebug.alertText2 = f'{maneuver.description}'
    else:
      alert_msg.alertDebug.alertText1 = 'Maneuvers Finished'

    pm.send('alertDebug', alert_msg)

    longitudinalPlan.aTarget = accel
    longitudinalPlan.shouldStop = v_ego < CP.vEgoStopping and accel < 1e-2

    longitudinalPlan.allowBrake = True
    longitudinalPlan.allowThrottle = True
    longitudinalPlan.hasLead = True

    longitudinalPlan.speeds = [0.2]  # triggers carControl.cruiseControl.resume in controlsd

    pm.send('longitudinalPlan', plan_send)

    assistance_send = messaging.new_message('driverAssistance')
    assistance_send.valid = True
    pm.send('driverAssistance', assistance_send)

    if maneuver is not None and maneuver.finished:
      maneuver = None
def update_events(self, CS):
    """Compute onroadEvents from carState"""

    self.events.clear()

    if self.sm['controlsState'].lateralControlState.which() == 'debugState':
      self.events.add(EventName.joystickDebug)
      self.startup_event = None

    if self.sm.recv_frame['lateralManeuverPlan'] > 0:
      self.events.add(EventName.lateralManeuver)
      self.startup_event = None
    elif self.sm.recv_frame['alertDebug'] > 0:
      self.events.add(EventName.longitudinalManeuver)
      self.startup_event = None

    # Add startup event
    if self.startup_event is not None:
      self.events.add(self.startup_event)
      self.startup_event = None

    # Don't add any more events if not initialized
    if not self.initialized:
      self.events.add(EventName.selfdriveInitializing)
      return

    # Check for user bookmark press (bookmark button or end of LKAS button feedback)
    if self.sm.updated['userBookmark']:
      self.events.add(EventName.userBookmark)

    if self.sm.updated['audioFeedback']:
      self.events.add(EventName.audioFeedback)

    # Don't add any more events while in dashcam mode
    if self.CP.passive:
      return

    # Block resume if cruise never previously enabled
    resume_pressed = any(be.type in (ButtonType.accelCruise, ButtonType.resumeCruise) for be in CS.buttonEvents)
    if not self.CP.pcmCruise and CS.vCruise > 250 and resume_pressed:
      self.events.add(EventName.resumeBlocked)

    # Handle DM
    if not self.CP.notCar:
      # Block engaging until ignition cycle after max number or time of distractions
      if self.sm['driverMonitoringState'].lockout and not self.dm_lockout_set:
        self.params.put_bool_nonblocking("DriverTooDistracted", True)
        self.dm_lockout_set = True
      # No entry conditions
      if self.sm['driverMonitoringState'].lockout or self.sm['driverMonitoringState'].alwaysOnLockout:
        self.events.add(EventName.tooDistracted)
      # Alerts
      vision_dm = self.sm['driverMonitoringState'].activePolicy == MonitoringPolicy.vision
      if self.sm['driverMonitoringState'].alertLevel == AlertLevel.one:
        self.events.add(EventName.driverDistracted1 if vision_dm else EventName.driverUnresponsive1)
      elif self.sm['driverMonitoringState'].alertLevel == AlertLevel.two:
        self.events.add(EventName.driverDistracted2 if vision_dm else EventName.driverUnresponsive2)
      elif self.sm['driverMonitoringState'].alertLevel == AlertLevel.three:
        self.events.add(EventName.driverDistracted3 if vision_dm else EventName.driverUnresponsive3)
      # Warn consistent DM uncertainty
      if self.sm['driverMonitoringState'].visionPolicyState.uncertainOffroadAlertPercent >= 100 and not self.dm_uncertain_alerted:
        set_offroad_alert("Offroad_DriverMonitoringUncertain", True)
        self.dm_uncertain_alerted = True

    # Add car events, ignore if CAN isn't valid
    if CS.canValid:
      car_events = self.car_events.update(CS, self.CS_prev, self.sm['carControl']).to_msg()
      self.events.add_from_msg(car_events)

      if self.CP.notCar:
        # wait for everything to init first
        if self.sm.frame > int(2. / DT_CTRL) and self.initialized:
          # body always wants to enable
          self.events.add(EventName.pcmEnable)

      # Disable on rising edge of accelerator or brake. Also disable on brake when speed > 0
      if (CS.gasPressed and not self.CS_prev.gasPressed and self.disengage_on_accelerator) or \
        (CS.brakePressed and (not self.CS_prev.brakePressed or not CS.standstill)) or \
        (CS.regenBraking and (not self.CS_prev.regenBraking or not CS.standstill)):
        self.events.add(EventName.pedalPressed)

    # Create events for temperature, disk space, and memory
    if self.sm['deviceState'].thermalStatus >= ThermalStatus.red:
      self.events.add(EventName.overheat)
    if self.sm['deviceState'].freeSpacePercent < 7 and not SIMULATION:
      self.events.add(EventName.outOfSpace)
    if self.sm['deviceState'].memoryUsagePercent > 90 and not SIMULATION:
      self.events.add(EventName.lowMemory)

    # Alert if fan isn't spinning for 5 seconds
    if self.sm['peripheralState'].pandaType != log.PandaState.PandaType.unknown:
      if self.sm['peripheralState'].fanSpeedRpm < 500 and self.sm['deviceState'].fanSpeedPercentDesired > 50:
        # allow enough time for the fan controller in the panda to recover from stalls
        if (self.sm.frame - self.last_functional_fan_frame) * DT_CTRL > 15.0:
          self.events.add(EventName.fanMalfunction)
      else:
        self.last_functional_fan_frame = self.sm.frame

    # Handle calibration status
    cal_status = self.sm['liveCalibration'].calStatus
    if cal_status != log.LiveCalibrationData.Status.calibrated:
      if cal_status == log.LiveCalibrationData.Status.uncalibrated:
        self.events.add(EventName.calibrationIncomplete)
      elif cal_status == log.LiveCalibrationData.Status.recalibrating:
        if not self.recalibrating_seen:
          set_offroad_alert("Offroad_Recalibration", True)
        self.recalibrating_seen = True
        self.events.add(EventName.calibrationRecalibrating)
      else:
        self.events.add(EventName.calibrationInvalid)

    # Lane departure warning
    if self.is_ldw_enabled and self.sm.valid['driverAssistance']:
      if self.sm['driverAssistance'].leftLaneDeparture or self.sm['driverAssistance'].rightLaneDeparture:
        self.events.add(EventName.ldw)

    # ******************************************************************************************
    #  NOTE: To fork maintainers.
    #  Disabling or nerfing safety features will get you and your users banned from our servers.
    #  We recommend that you do not change these numbers from the defaults.
    if self.sm.updated['liveCalibration']:
      self.pose_calibrator.feed_live_calib(self.sm['liveCalibration'])
    if self.sm.updated['livePose']:
      device_pose = Pose.from_live_pose(self.sm['livePose'])
      self.calibrated_pose = self.pose_calibrator.build_calibrated_pose(device_pose)

    if self.calibrated_pose is not None:
      excessive_actuation = self.excessive_actuation_check.update(self.sm, CS, self.calibrated_pose)
      if not self.excessive_actuation and excessive_actuation is not None:
        set_offroad_alert("Offroad_ExcessiveActuation", True, extra_text=str(excessive_actuation))
        self.excessive_actuation = True

    if self.excessive_actuation:
      self.events.add(EventName.excessiveActuation)
    # ******************************************************************************************

    # Handle lane change
    if self.sm['modelV2'].meta.laneChangeState == LaneChangeState.preLaneChange:
      direction = self.sm['modelV2'].meta.laneChangeDirection
      if (CS.leftBlindspot and direction == LaneChangeDirection.left) or \
         (CS.rightBlindspot and direction == LaneChangeDirection.right):
        self.events.add(EventName.laneChangeBlocked)
      else:
        if direction == LaneChangeDirection.left:
          self.events.add(EventName.preLaneChangeLeft)
        else:
          self.events.add(EventName.preLaneChangeRight)
    elif self.sm['modelV2'].meta.laneChangeState in (LaneChangeState.laneChangeStarting,
                                                    LaneChangeState.laneChangeFinishing):
      self.events.add(EventName.laneChange)

    for i, pandaState in enumerate(self.sm['pandaStates']):
      # All pandas must match the list of safetyConfigs, and if outside this list, must be silent or noOutput
      if i < len(self.CP.safetyConfigs):
        safety_mismatch = pandaState.safetyModel != self.CP.safetyConfigs[i].safetyModel or \
                          pandaState.safetyParam != self.CP.safetyConfigs[i].safetyParam or \
                          pandaState.alternativeExperience != self.CP.alternativeExperience
      else:
        safety_mismatch = pandaState.safetyModel not in IGNORED_SAFETY_MODES

      # safety mismatch allows some time for pandad to set the safety mode and publish it back from panda
      if (safety_mismatch and self.sm.frame*DT_CTRL > 10.) or pandaState.safetyRxChecksInvalid or self.mismatch_counter >= 200:
        self.events.add(EventName.controlsMismatch)

      if log.PandaState.FaultType.relayMalfunction in pandaState.faults:
        self.events.add(EventName.relayMalfunction)

    # Handle HW and system malfunctions
    # Order is very intentional here. Be careful when modifying this.
    # All events here should at least have NO_ENTRY and SOFT_DISABLE.
    num_events = len(self.events)

    not_running = {p.name for p in self.sm['managerState'].processes if not p.running and p.shouldBeRunning}
    if self.sm.recv_frame['managerState'] and len(not_running):
      if not_running != self.not_running_prev:
        cloudlog.event("process_not_running", not_running=not_running, error=True)
      self.not_running_prev = not_running
    if self.sm.recv_frame['managerState'] and not_running:
      self.events.add(EventName.processNotRunning)
    else:
      if not SIMULATION and not self.rk.lagging:
        if not self.sm.all_alive(self.camera_packets):
          self.events.add(EventName.cameraMalfunction)
        elif not self.sm.all_freq_ok(self.camera_packets):
          self.events.add(EventName.cameraFrameRate)
    if not REPLAY and self.rk.lagging:
      self.events.add(EventName.selfdrivedLagging)
    if self.sm['radarState'].radarErrors.canError:
      self.events.add(EventName.canError)
    elif self.sm['radarState'].radarErrors.radarUnavailableTemporary:
      self.events.add(EventName.radarTempUnavailable)
    elif any(self.sm['radarState'].radarErrors.to_dict().values()):
      self.events.add(EventName.radarFault)
    if not self.sm.valid['pandaStates']:
      self.events.add(EventName.usbError)
    if CS.canTimeout:
      self.events.add(EventName.canBusMissing)
    elif not CS.canValid:
      self.events.add(EventName.canError)

    # generic catch-all. ideally, a more specific event should be added above instead
    has_disable_events = self.events.contains(ET.NO_ENTRY) and (self.events.contains(ET.SOFT_DISABLE) or self.events.contains(ET.IMMEDIATE_DISABLE))
    no_system_errors = (not has_disable_events) or (len(self.events) == num_events)
    if not self.sm.all_checks() and no_system_errors:
      if not self.sm.all_alive():
        self.events.add(EventName.commIssue)
      elif not self.sm.all_freq_ok():
        self.events.add(EventName.commIssueAvgFreq)
      else:
        self.events.add(EventName.commIssue)

      logs = {
        'invalid': [s for s, valid in self.sm.valid.items() if not valid],
        'not_alive': [s for s, alive in self.sm.alive.items() if not alive],
        'not_freq_ok': [s for s, freq_ok in self.sm.freq_ok.items() if not freq_ok],
      }
      if logs != self.logged_comm_issue:
        cloudlog.event("commIssue", error=True, **logs)
        self.logged_comm_issue = logs
    else:
      self.logged_comm_issue = None

    if not self.CP.notCar:
      if not self.sm['livePose'].posenetOK:
        self.events.add(EventName.posenetInvalid)
      if not self.sm['livePose'].inputsOK:
        self.events.add(EventName.locationdTemporaryError)
      if not self.sm['liveParameters'].valid and cal_status == log.LiveCalibrationData.Status.calibrated and not TESTING_CLOSET and (not SIMULATION or REPLAY):
        self.events.add(EventName.paramsdTemporaryError)

    # conservative HW alert. if the data or frequency are off, locationd will throw an error
    if any((self.sm.frame - self.sm.recv_frame[s])*DT_CTRL > 10. for s in self.sensor_packets):
      self.events.add(EventName.sensorDataInvalid)

    if not REPLAY:
      # Check for mismatch between openpilot and car's PCM
      cruise_mismatch = CS.cruiseState.enabled and (not self.enabled or not self.CP.pcmCruise)
      self.cruise_mismatch_counter = self.cruise_mismatch_counter + 1 if cruise_mismatch else 0
      if self.cruise_mismatch_counter > int(6. / DT_CTRL):
        self.events.add(EventName.cruiseMismatch)

    # Send a "steering required alert" if saturation count has reached the limit
    if CS.steeringPressed:
      self.last_steering_pressed_frame = self.sm.frame
    recent_steer_pressed = (self.sm.frame - self.last_steering_pressed_frame)*DT_CTRL < 2.0
    controlstate = self.sm['controlsState']
    lac = getattr(controlstate.lateralControlState, controlstate.lateralControlState.which())
    if lac.active and not recent_steer_pressed and not self.CP.notCar:
      clipped_speed = max(CS.vEgo, 0.3)
      actual_lateral_accel = controlstate.curvature * (clipped_speed**2)
      desired_lateral_accel = self.sm['modelV2'].action.desiredCurvature * (clipped_speed**2)
      undershooting = abs(desired_lateral_accel) / abs(1e-3 + actual_lateral_accel) > 1.2
      turning = abs(desired_lateral_accel) > 1.0
      # TODO: lac.saturated includes speed and other checks, should be pulled out
      if undershooting and turning and lac.saturated:
        self.events.add(EventName.steerSaturated)

    # Check for FCW
    stock_long_is_braking = self.enabled and not self.CP.openpilotLongitudinalControl and CS.aEgo < -1.25
    model_fcw = self.sm['modelV2'].meta.hardBrakePredicted and not CS.brakePressed and not stock_long_is_braking
    planner_fcw = self.sm['longitudinalPlan'].fcw and self.enabled
    if (planner_fcw or model_fcw) and not self.CP.notCar:
      self.events.add(EventName.fcw)

    # GPS checks
    gps_ok = self.sm.recv_frame[self.gps_location_service] > 0 and (self.sm.frame - self.sm.recv_frame[self.gps_location_service]) * DT_CTRL < 2.0
    if not gps_ok and self.sm['livePose'].inputsOK and (self.distance_traveled > 1500):
      self.events.add(EventName.noGps)
    if gps_ok:
      self.distance_traveled = 0
    self.distance_traveled += abs(CS.vEgo) * DT_CTRL

    # TODO: fix simulator
    if not SIMULATION or REPLAY:
      if self.sm['modelV2'].frameDropPerc > 20:
        self.events.add(EventName.modeldLagging)

    # Decrement personality on distance button press
    if self.CP.openpilotLongitudinalControl:
      if any(not be.pressed and be.type == ButtonType.gapAdjustCruise for be in CS.buttonEvents):
        self.personality = (self.personality - 1) % 3
        self.params.put_nonblocking('LongitudinalPersonality', self.personality)
        self.events.add(EventName.personalityChanged)
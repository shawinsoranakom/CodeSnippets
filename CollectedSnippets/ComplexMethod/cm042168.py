def __init__(self, CP=None):
    self.params = Params()

    # Ensure the current branch is cached, otherwise the first cycle lags
    build_metadata = get_build_metadata()

    if CP is None:
      cloudlog.info("selfdrived is waiting for CarParams")
      self.CP = messaging.log_from_bytes(self.params.get("CarParams", block=True), car.CarParams)
      cloudlog.info("selfdrived got CarParams")
    else:
      self.CP = CP

    self.car_events = CarSpecificEvents(self.CP)

    self.pose_calibrator = PoseCalibrator()
    self.calibrated_pose: Pose | None = None
    self.excessive_actuation_check = ExcessiveActuationCheck()
    self.excessive_actuation = self.params.get("Offroad_ExcessiveActuation") is not None

    # Setup sockets
    self.pm = messaging.PubMaster(['selfdriveState', 'onroadEvents'])

    self.gps_location_service = get_gps_location_service(self.params)
    self.gps_packets = [self.gps_location_service]
    self.sensor_packets = ["accelerometer", "gyroscope"]
    self.camera_packets = ["roadCameraState", "driverCameraState", "wideRoadCameraState"]

    # TODO: de-couple selfdrived with card/conflate on carState without introducing controls mismatches
    self.car_state_sock = messaging.sub_sock('carState', timeout=20)

    ignore = self.sensor_packets + self.gps_packets + ['alertDebug', 'lateralManeuverPlan']
    if SIMULATION:
      ignore += ['driverCameraState', 'managerState']
    if REPLAY:
      # no vipc in replay will make them ignored anyways
      ignore += ['roadCameraState', 'wideRoadCameraState']
    self.sm = messaging.SubMaster(['deviceState', 'pandaStates', 'peripheralState', 'modelV2', 'liveCalibration',
                                   'carOutput', 'driverMonitoringState', 'longitudinalPlan', 'livePose', 'liveDelay',
                                   'managerState', 'liveParameters', 'radarState', 'liveTorqueParameters',
                                   'controlsState', 'carControl', 'driverAssistance', 'alertDebug', 'userBookmark', 'audioFeedback',
                                   'lateralManeuverPlan'] + \
                                   self.camera_packets + self.sensor_packets + self.gps_packets,
                                  ignore_alive=ignore, ignore_avg_freq=ignore,
                                  ignore_valid=ignore, frequency=int(1/DT_CTRL))

    # read params
    self.is_metric = self.params.get_bool("IsMetric")
    self.is_ldw_enabled = self.params.get_bool("IsLdwEnabled")
    self.disengage_on_accelerator = self.params.get_bool("DisengageOnAccelerator")

    car_recognized = self.CP.brand != 'mock'

    # cleanup old params
    if not self.CP.alphaLongitudinalAvailable:
      self.params.remove("AlphaLongitudinalEnabled")
    if not self.CP.openpilotLongitudinalControl:
      self.params.remove("ExperimentalMode")

    self.CS_prev = car.CarState.new_message()
    self.AM = AlertManager()
    self.events = Events()

    self.initialized = False
    self.enabled = False
    self.active = False
    self.mismatch_counter = 0
    self.cruise_mismatch_counter = 0
    self.last_steering_pressed_frame = 0
    self.distance_traveled = 0
    self.last_functional_fan_frame = 0
    self.events_prev = []
    self.logged_comm_issue = None
    self.not_running_prev = None
    self.experimental_mode = False
    self.personality = self.params.get("LongitudinalPersonality", return_default=True)
    self.recalibrating_seen = False
    self.dm_lockout_set = False
    self.dm_uncertain_alerted = False
    self.state_machine = StateMachine()
    self.rk = Ratekeeper(100, print_delay_threshold=None)

    # Determine startup event
    self.startup_event = EventName.startup if build_metadata.openpilot.comma_remote and build_metadata.tested_channel else EventName.startupMaster
    if HARDWARE.get_device_type() == 'mici':
      self.startup_event = None
    if not car_recognized:
      self.startup_event = EventName.startupNoCar
    elif car_recognized and self.CP.passive:
      self.startup_event = EventName.startupNoControl
    elif self.CP.secOcRequired and not self.CP.secOcKeyAvailable:
      self.startup_event = EventName.startupNoSecOcKey

    if not car_recognized:
      self.events.add(EventName.carUnrecognized, static=True)
      set_offroad_alert("Offroad_CarUnrecognized", True)
    elif self.CP.passive:
      self.events.add(EventName.dashcamMode, static=True)
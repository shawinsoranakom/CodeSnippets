def fill_model_msg(base_msg: capnp._DynamicStructBuilder, extended_msg: capnp._DynamicStructBuilder,
                   net_output_data: dict[str, np.ndarray], action: log.ModelDataV2.Action,
                   publish_state: PublishState, vipc_frame_id: int, vipc_frame_id_extra: int,
                   frame_id: int, frame_drop: float, timestamp_eof: int, model_execution_time: float,
                   valid: bool) -> None:
  frame_age = frame_id - vipc_frame_id if frame_id > vipc_frame_id else 0
  frame_drop_perc = frame_drop * 100
  extended_msg.valid = valid
  base_msg.valid = valid

  driving_model_data = base_msg.drivingModelData

  driving_model_data.frameId = vipc_frame_id
  driving_model_data.frameIdExtra = vipc_frame_id_extra
  driving_model_data.frameDropPerc = frame_drop_perc
  driving_model_data.modelExecutionTime = model_execution_time

  driving_model_data.action = action

  modelV2 = extended_msg.modelV2
  modelV2.frameId = vipc_frame_id
  modelV2.frameIdExtra = vipc_frame_id_extra
  modelV2.frameAge = frame_age
  modelV2.frameDropPerc = frame_drop_perc
  modelV2.timestampEof = timestamp_eof
  modelV2.modelExecutionTime = model_execution_time

  # plan
  fill_xyzt(modelV2.position, ModelConstants.T_IDXS, *net_output_data['plan'][0,:,Plan.POSITION].T, *net_output_data['plan_stds'][0,:,Plan.POSITION].T)
  fill_xyzt(modelV2.velocity, ModelConstants.T_IDXS, *net_output_data['plan'][0,:,Plan.VELOCITY].T)
  fill_xyzt(modelV2.acceleration, ModelConstants.T_IDXS, *net_output_data['plan'][0,:,Plan.ACCELERATION].T)
  fill_xyzt(modelV2.orientation, ModelConstants.T_IDXS, *net_output_data['plan'][0,:,Plan.T_FROM_CURRENT_EULER].T)
  fill_xyzt(modelV2.orientationRate, ModelConstants.T_IDXS, *net_output_data['plan'][0,:,Plan.ORIENTATION_RATE].T)

  # poly path
  fill_xyz_poly(driving_model_data.path, ModelConstants.POLY_PATH_DEGREE, *net_output_data['plan'][0,:,Plan.POSITION].T)

  # action
  modelV2.action = action

  # times at X_IDXS of edges and lines aren't used
  LINE_T_IDXS: list[float] = []

  # lane lines
  modelV2.init('laneLines', 4)
  for i in range(4):
    lane_line = modelV2.laneLines[i]
    fill_xyzt(lane_line, LINE_T_IDXS, np.array(ModelConstants.X_IDXS), net_output_data['lane_lines'][0,i,:,0], net_output_data['lane_lines'][0,i,:,1])
  modelV2.laneLineStds = net_output_data['lane_lines_stds'][0,:,0,0].tolist()
  modelV2.laneLineProbs = net_output_data['lane_lines_prob'][0,1::2].tolist()

  fill_lane_line_meta(driving_model_data.laneLineMeta, modelV2.laneLines, modelV2.laneLineProbs)

  # road edges
  modelV2.init('roadEdges', 2)
  for i in range(2):
    road_edge = modelV2.roadEdges[i]
    fill_xyzt(road_edge, LINE_T_IDXS, np.array(ModelConstants.X_IDXS), net_output_data['road_edges'][0,i,:,0], net_output_data['road_edges'][0,i,:,1])
  modelV2.roadEdgeStds = net_output_data['road_edges_stds'][0,:,0,0].tolist()

  # leads
  modelV2.init('leadsV3', 3)
  for i in range(3):
    lead = modelV2.leadsV3[i]
    fill_xyvat(lead, ModelConstants.LEAD_T_IDXS, *net_output_data['lead'][0,i].T, *net_output_data['lead_stds'][0,i].T)
    lead.prob = net_output_data['lead_prob'][0,i].tolist()
    lead.probTime = ModelConstants.LEAD_T_OFFSETS[i]

  # meta
  meta = modelV2.meta
  meta.desireState = net_output_data['desire_state'][0].reshape(-1).tolist()
  meta.desirePrediction = net_output_data['desire_pred'][0].reshape(-1).tolist()
  meta.engagedProb = net_output_data['meta'][0,Meta.ENGAGED].item()
  meta.init('disengagePredictions')
  disengage_predictions = meta.disengagePredictions
  disengage_predictions.t = ModelConstants.META_T_IDXS
  disengage_predictions.brakeDisengageProbs = net_output_data['meta'][0,Meta.BRAKE_DISENGAGE].tolist()
  disengage_predictions.gasDisengageProbs = net_output_data['meta'][0,Meta.GAS_DISENGAGE].tolist()
  disengage_predictions.steerOverrideProbs = net_output_data['meta'][0,Meta.STEER_OVERRIDE].tolist()
  disengage_predictions.brake3MetersPerSecondSquaredProbs = net_output_data['meta'][0,Meta.HARD_BRAKE_3].tolist()
  disengage_predictions.brake4MetersPerSecondSquaredProbs = net_output_data['meta'][0,Meta.HARD_BRAKE_4].tolist()
  disengage_predictions.brake5MetersPerSecondSquaredProbs = net_output_data['meta'][0,Meta.HARD_BRAKE_5].tolist()
  disengage_predictions.gasPressProbs = net_output_data['meta'][0,Meta.GAS_PRESS].tolist()
  disengage_predictions.brakePressProbs = net_output_data['meta'][0,Meta.BRAKE_PRESS].tolist()

  publish_state.prev_brake_5ms2_probs[:-1] = publish_state.prev_brake_5ms2_probs[1:]
  publish_state.prev_brake_5ms2_probs[-1] = net_output_data['meta'][0,Meta.HARD_BRAKE_5][0]
  publish_state.prev_brake_3ms2_probs[:-1] = publish_state.prev_brake_3ms2_probs[1:]
  publish_state.prev_brake_3ms2_probs[-1] = net_output_data['meta'][0,Meta.HARD_BRAKE_3][0]
  hard_brake_predicted = (publish_state.prev_brake_5ms2_probs > ModelConstants.FCW_THRESHOLDS_5MS2).all() and \
    (publish_state.prev_brake_3ms2_probs > ModelConstants.FCW_THRESHOLDS_3MS2).all()
  meta.hardBrakePredicted = hard_brake_predicted.item()

  # confidence
  if vipc_frame_id % (2*ModelConstants.MODEL_RUN_FREQ) == 0:
    # any disengage prob
    brake_disengage_probs = net_output_data['meta'][0,Meta.BRAKE_DISENGAGE]
    gas_disengage_probs = net_output_data['meta'][0,Meta.GAS_DISENGAGE]
    steer_override_probs = net_output_data['meta'][0,Meta.STEER_OVERRIDE]
    any_disengage_probs = 1-((1-brake_disengage_probs)*(1-gas_disengage_probs)*(1-steer_override_probs))
    # independent disengage prob for each 2s slice
    ind_disengage_probs = np.r_[any_disengage_probs[0], np.diff(any_disengage_probs) / (1 - any_disengage_probs[:-1])]
    # rolling buf for 2, 4, 6, 8, 10s
    publish_state.disengage_buffer[:-ModelConstants.DISENGAGE_WIDTH] = publish_state.disengage_buffer[ModelConstants.DISENGAGE_WIDTH:]
    publish_state.disengage_buffer[-ModelConstants.DISENGAGE_WIDTH:] = ind_disengage_probs

  score = 0.
  for i in range(ModelConstants.DISENGAGE_WIDTH):
    score += publish_state.disengage_buffer[i*ModelConstants.DISENGAGE_WIDTH+ModelConstants.DISENGAGE_WIDTH-1-i].item() / ModelConstants.DISENGAGE_WIDTH
  if score < ModelConstants.RYG_GREEN:
    modelV2.confidence = ConfidenceClass.green
  elif score < ModelConstants.RYG_YELLOW:
    modelV2.confidence = ConfidenceClass.yellow
  else:
    modelV2.confidence = ConfidenceClass.red

  # raw prediction if enabled
  if SEND_RAW_PRED:
    modelV2.rawPredictions = net_output_data['raw_pred'].tobytes()
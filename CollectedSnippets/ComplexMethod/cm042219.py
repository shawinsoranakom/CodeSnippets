def migrate_drivingModelData(msgs):
  add_ops = []
  for _, msg in msgs:
    dmd = messaging.new_message('drivingModelData', valid=msg.valid, logMonoTime=msg.logMonoTime)
    for field in ["frameId", "frameIdExtra", "frameDropPerc", "modelExecutionTime", "action"]:
      setattr(dmd.drivingModelData, field, getattr(msg.modelV2, field))
    for meta_field in ["laneChangeState", "laneChangeState"]:
      setattr(dmd.drivingModelData.meta, meta_field, getattr(msg.modelV2.meta, meta_field))
    if len(msg.modelV2.laneLines) and len(msg.modelV2.laneLineProbs):
      fill_lane_line_meta(dmd.drivingModelData.laneLineMeta, msg.modelV2.laneLines, msg.modelV2.laneLineProbs)
    if all(len(a) for a in [msg.modelV2.position.x, msg.modelV2.position.y, msg.modelV2.position.z]):
      fill_xyz_poly(dmd.drivingModelData.path, ModelConstants.POLY_PATH_DEGREE, msg.modelV2.position.x, msg.modelV2.position.y, msg.modelV2.position.z)
    add_ops.append( dmd.as_reader())
  return [], add_ops, []
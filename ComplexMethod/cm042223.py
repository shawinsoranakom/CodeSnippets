def migrate_sensorEvents(msgs):
  add_ops, del_ops = [], []
  for index, msg in msgs:
    # migrate to split sensor events
    for evt in msg.sensorEventsDEPRECATED:
      # build new message for each sensor type
      sensor_service = ''
      if evt.which() == 'acceleration':
        sensor_service = 'accelerometer'
      elif evt.which() == 'gyro' or evt.which() == 'gyroUncalibrated':
        sensor_service = 'gyroscope'
      elif evt.which() == 'light' or evt.which() == 'proximity':
        sensor_service = 'lightSensor'
      elif evt.which() == 'magnetic' or evt.which() == 'magneticUncalibrated':
        sensor_service = 'magnetometer'
      elif evt.which() == 'temperature':
        sensor_service = 'temperatureSensor'

      m = messaging.new_message(sensor_service)
      m.valid = True
      m.logMonoTime = msg.logMonoTime

      m_dat = getattr(m, sensor_service)
      m_dat.source = evt.source
      m_dat.timestamp = evt.timestamp
      setattr(m_dat, evt.which(), getattr(evt, evt.which()))

      add_ops.append(m.as_reader())
    del_ops.append(index)
  return [], add_ops, del_ops
def main() -> None:
  config_realtime_process([1, ], 1)

  sensors_cfg = [
    (LSM6DS3_Accel(I2C_BUS_IMU), "accelerometer", True),
    (LSM6DS3_Gyro(I2C_BUS_IMU), "gyroscope", True),
    (LSM6DS3_Temp(I2C_BUS_IMU), "temperatureSensor", False),
  ]

  # Reset sensors
  for sensor, _, _ in sensors_cfg:
    try:
      sensor.reset()
    except Exception:
      cloudlog.exception(f"Error initializing {sensor} sensor")

  # Initialize sensors
  exit_event = threading.Event()
  threads = [
    threading.Thread(target=interrupt_loop, args=(sensors_cfg, exit_event), daemon=True)
  ]
  for sensor, service, interrupt in sensors_cfg:
    try:
      sensor.init()
      if not interrupt:
        # Start polling thread for sensors without interrupts
        threads.append(threading.Thread(
          target=polling_loop,
          args=(sensor, service, exit_event),
          daemon=True
        ))
    except Exception:
      cloudlog.exception(f"Error initializing {service} sensor")

  try:
    for t in threads:
      t.start()
    while any(t.is_alive() for t in threads):
      time.sleep(1)
  except KeyboardInterrupt:
    pass
  finally:
    exit_event.set()
    for t in threads:
      if t.is_alive():
        t.join()

    for sensor, _, _ in sensors_cfg:
      try:
        sensor.shutdown()
      except Exception:
        cloudlog.exception("Error shutting down sensor")
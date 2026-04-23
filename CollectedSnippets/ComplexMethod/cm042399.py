def _run(self):
    while not self._stop_event.is_set():
      if self._should_check():
        try:
          request = urllib.request.Request(OPENPILOT_URL, method="HEAD")
          urllib.request.urlopen(request, timeout=2.0)

          # Discard stale result if invalidated during request
          if self.recheck_event.is_set():
            self.recheck_event.clear()
            continue

          self.network_connected.set()
          if HARDWARE.get_network_type() == NetworkType.wifi:
            self.wifi_connected.set()
        except urllib.error.URLError as e:
          if (isinstance(e.reason, ssl.SSLCertVerificationError) and
              not system_time_valid() and
              time.monotonic() - self._last_timesyncd_restart > 5):
            self._last_timesyncd_restart = time.monotonic()
            run_cmd(["sudo", "systemctl", "restart", "systemd-timesyncd"])
          self.reset()
        except Exception:
          self.reset()
      else:
        self.reset()

      if self._stop_event.wait(timeout=1.0):
        break
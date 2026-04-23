def _download_thread(self):
    try:
      import tempfile

      fd, tmpfile = tempfile.mkstemp(prefix="installer_")

      headers = {"User-Agent": USER_AGENT,
                 "X-openpilot-serial": HARDWARE.get_serial(),
                 "X-openpilot-device-type": HARDWARE.get_device_type()}
      req = urllib.request.Request(self.download_url, headers=headers)

      with open(tmpfile, 'wb') as f, urllib.request.urlopen(req, timeout=30) as response:
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        block_size = 8192

        while True:
          buffer = response.read(block_size)
          if not buffer:
            break

          downloaded += len(buffer)
          f.write(buffer)

          if total_size:
            self.download_progress = int(downloaded * 100 / total_size)

      is_elf = False
      with open(tmpfile, 'rb') as f:
        header = f.read(4)
        is_elf = header == b'\x7fELF'

      if not is_elf:
        self._download_failed_reason = "No custom software found at this URL: " + self.download_url.replace("https://", "", 1)
        return

      # NOTE: currently unused, for future logging
      with open(INSTALLER_URL_PATH, "w") as f:
        f.write(self.download_url)

      # AGNOS might try to execute the installer before this process exits.
      # Therefore, important to close the fd before renaming the installer.
      os.close(fd)
      os.rename(tmpfile, INSTALLER_DESTINATION_PATH)

      # give time for installer UI to take over
      time.sleep(0.1)
      gui_app.request_close()

    except urllib.error.HTTPError as e:
      if e.code == 409:
        self._download_failed_reason = "Incompatible openpilot version."
    except Exception:
      self._download_failed_reason = "Invalid URL: " + self.download_url.replace("https://", "", 1)
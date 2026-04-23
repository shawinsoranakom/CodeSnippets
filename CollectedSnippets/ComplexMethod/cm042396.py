def _render(self, rect: rl.Rectangle):
    if self.state == SetupState.LOW_VOLTAGE:
      self.render_low_voltage(rect)
    elif self.state == SetupState.GETTING_STARTED:
      self.render_getting_started(rect)
    elif self.state == SetupState.NETWORK_SETUP:
      self.render_network_setup(rect)
    elif self.state == SetupState.SOFTWARE_SELECTION:
      self.render_software_selection(rect)
    elif self.state == SetupState.CUSTOM_SOFTWARE_WARNING:
      self.render_custom_software_warning(rect)
    elif self.state == SetupState.CUSTOM_SOFTWARE:
      self.render_custom_software()
    elif self.state == SetupState.DOWNLOADING:
      self.render_downloading(rect)
    elif self.state == SetupState.DOWNLOAD_FAILED:
      self.render_download_failed(rect)
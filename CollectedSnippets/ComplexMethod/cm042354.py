def configure_modem(self):
    sim_id = self.get_sim_info().get('sim_id', '')

    cmds = []
    modem = self.get_modem()

    # Quectel EG25
    if self.get_device_type() in ("tizi", ):
      # clear out old blue prime initial APN
      os.system('mmcli -m any --3gpp-set-initial-eps-bearer-settings="apn="')

      cmds += [
        # SIM hot swap
        'AT+QSIMDET=1,0',
        'AT+QSIMSTAT=1',

        # configure modem as data-centric
        'AT+QNVW=5280,0,"0102000000000000"',
        'AT+QNVFW="/nv/item_files/ims/IMS_enable",00',
        'AT+QNVFW="/nv/item_files/modem/mmode/ue_usage_setting",01',
      ]

    # Quectel EG916
    else:
      # this modem gets upset with too many AT commands
      if sim_id is None or len(sim_id) == 0:
        cmds += [
          # SIM sleep disable
          'AT$QCSIMSLEEP=0',
          'AT$QCSIMCFG=SimPowerSave,0',

          # ethernet config
          'AT$QCPCFG=usbNet,1',
        ]

    for cmd in cmds:
      try:
        modem.Command(cmd, math.ceil(TIMEOUT), dbus_interface=MM_MODEM, timeout=TIMEOUT)
      except Exception:
        pass

    # eSIM prime
    dest = "/etc/NetworkManager/system-connections/esim.nmconnection"
    if self.get_sim_lpa().is_comma_profile(sim_id) and not os.path.exists(dest):
      with open(Path(__file__).parent/'esim.nmconnection') as f, tempfile.NamedTemporaryFile(mode='w') as tf:
        dat = f.read()
        dat = dat.replace("sim-id=", f"sim-id={sim_id}")
        tf.write(dat)
        tf.flush()

        # needs to be root
        os.system(f"sudo cp {tf.name} {dest}")
      os.system(f"sudo nmcli con load {dest}")
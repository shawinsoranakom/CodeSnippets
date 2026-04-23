def testBluetoothConstants(self):
        socket.BDADDR_ANY
        socket.BDADDR_LOCAL
        socket.AF_BLUETOOTH
        socket.BTPROTO_RFCOMM
        socket.SOL_RFCOMM

        if sys.platform == "win32":
            socket.SO_BTH_ENCRYPT
            socket.SO_BTH_MTU
            socket.SO_BTH_MTU_MAX
            socket.SO_BTH_MTU_MIN

        if sys.platform != "win32":
            socket.BTPROTO_HCI
            socket.SOL_HCI
            socket.BTPROTO_L2CAP
            socket.SOL_L2CAP
            socket.BTPROTO_SCO
            socket.SOL_SCO
            socket.HCI_DATA_DIR

        if sys.platform == "linux":
            socket.SOL_BLUETOOTH
            socket.HCI_DEV_NONE
            socket.HCI_CHANNEL_RAW
            socket.HCI_CHANNEL_USER
            socket.HCI_CHANNEL_MONITOR
            socket.HCI_CHANNEL_CONTROL
            socket.HCI_CHANNEL_LOGGING
            socket.HCI_TIME_STAMP
            socket.BT_SECURITY
            socket.BT_SECURITY_SDP
            socket.BT_FLUSHABLE
            socket.BT_POWER
            socket.BT_CHANNEL_POLICY
            socket.BT_CHANNEL_POLICY_BREDR_ONLY
            if hasattr(socket, 'BT_PHY'):
                socket.BT_PHY_BR_1M_1SLOT
            if hasattr(socket, 'BT_MODE'):
                socket.BT_MODE_BASIC
            if hasattr(socket, 'BT_VOICE'):
                socket.BT_VOICE_TRANSPARENT
                socket.BT_VOICE_CVSD_16BIT
            socket.L2CAP_LM
            socket.L2CAP_LM_MASTER
            socket.L2CAP_LM_AUTH

        if sys.platform in ("linux", "freebsd"):
            socket.BDADDR_BREDR
            socket.BDADDR_LE_PUBLIC
            socket.BDADDR_LE_RANDOM
            socket.HCI_FILTER

        if sys.platform.startswith(("freebsd", "netbsd", "dragonfly")):
            socket.SO_L2CAP_IMTU
            socket.SO_L2CAP_FLUSH
            socket.SO_RFCOMM_MTU
            socket.SO_RFCOMM_FC_INFO
            socket.SO_SCO_MTU

        if sys.platform == "freebsd":
            socket.SO_SCO_CONNINFO

        if sys.platform.startswith(("netbsd", "dragonfly")):
            socket.SO_HCI_EVT_FILTER
            socket.SO_HCI_PKT_FILTER
            socket.SO_L2CAP_IQOS
            socket.SO_L2CAP_LM
            socket.L2CAP_LM_AUTH
            socket.SO_RFCOMM_LM
            socket.RFCOMM_LM_AUTH
            socket.SO_SCO_HANDLE
def __init__(self):
        self.installation_id_v3 = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, _get_machine_id_v3())
        )
def __init__(self, client: SessionClient, session: AppSession):
        """Initialize a SessionInfo instance.

        Parameters
        ----------
        session : AppSession
            The AppSession object.
        client : SessionClient
            The concrete SessionClient for this session.
        """
        self.session = session
        self.client = client
        self.script_run_count = 0
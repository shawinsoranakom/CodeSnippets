def project_state(self, nodes=None, at_end=True):
        """
        Return a ProjectState object representing the most recent state
        that the loaded migrations represent.

        See graph.make_state() for the meaning of "nodes" and "at_end".
        """
        return self.graph.make_state(
            nodes=nodes, at_end=at_end, real_apps=self.unmigrated_apps
        )
def _compute_current_session(self):
        """If there is an open session, store it to current_session_id / current_session_State.
        """
        self.session_ids.fetch(["state"])
        for pos_config in self:
            opened_sessions = pos_config.session_ids.filtered(lambda s: s.state != 'closed')
            rescue_sessions = opened_sessions.filtered('rescue')
            session = pos_config.session_ids.filtered(lambda s: s.state != 'closed' and not s.rescue)
            # sessions ordered by id desc
            pos_config.has_active_session = opened_sessions and True or False
            pos_config.current_session_id = session and session[0].id or False
            pos_config.current_session_state = session and session[0].state or False
            pos_config.number_of_rescue_session = len(rescue_sessions)
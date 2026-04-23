def _save_session(self, env=None):
        """
        Save a modified session on disk.

        :param env: an environment to compute the session token.
            MUST be left ``None`` (in which case it uses the request's
            env) UNLESS the database changed.
        """
        sess = self.session
        if env is None:
            env = self.env

        if not sess.can_save:
            return

        if sess.should_rotate:
            root.session_store.rotate(sess, env)  # it saves
        elif (
            sess.uid
            and time.time() >= sess['create_time'] + SESSION_ROTATION_INTERVAL
            and request.httprequest.path not in SESSION_ROTATION_EXCLUDED_PATHS
        ):
            root.session_store.rotate(sess, env, True)
        elif sess.is_dirty:
            root.session_store.save(sess)

        cookie_sid = self.cookies.get('session_id')
        if sess.is_dirty or cookie_sid != sess.sid:
            self.future_response.set_cookie(
                'session_id',
                sess.sid,
                max_age=get_session_max_inactivity(env),
                httponly=True
            )
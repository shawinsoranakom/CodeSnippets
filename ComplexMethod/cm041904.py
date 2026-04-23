def _execute_env_action(self, action: EnvAction):
        action_type = action.action_type
        res = None
        if action_type == EnvActionType.NONE:
            pass
        elif action_type == EnvActionType.SYSTEM_BACK:
            res = self.system_back()
        elif action_type == EnvActionType.SYSTEM_TAP:
            res = self.system_tap(x=action.coord[0], y=action.coord[1])
        elif action_type == EnvActionType.USER_INPUT:
            res = self.user_input(input_txt=action.input_txt)
        elif action_type == EnvActionType.USER_LONGPRESS:
            res = self.user_longpress(x=action.coord[0], y=action.coord[1])
        elif action_type == EnvActionType.USER_SWIPE:
            res = self.user_swipe(x=action.coord[0], y=action.coord[1], orient=action.orient, dist=action.dist)
        elif action_type == EnvActionType.USER_SWIPE_TO:
            res = self.user_swipe_to(start=action.coord, end=action.tgt_coord)
        return res
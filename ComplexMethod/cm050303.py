def _get_write_values(self, new_value):
        """Generate values to write after recomputation of a goal score"""
        if new_value == self.current:
            # avoid useless write if the new value is the same as the old one
            return {}

        result = {'current': new_value}
        if (self.definition_id.condition == 'higher' and new_value >= self.target_goal) \
          or (self.definition_id.condition == 'lower' and new_value <= self.target_goal):
            # success, do no set closed as can still change
            result['state'] = 'reached'

        elif self.end_date and fields.Date.today() > self.end_date:
            # check goal failure
            result['state'] = 'failed'
            result['closed'] = True

        return {self: result}
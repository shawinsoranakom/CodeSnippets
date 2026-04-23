def _compute_color(self):
        """Set the color based on the goal's state and completion"""
        for goal in self:
            goal.color = 0
            if (goal.end_date and goal.last_update):
                if (goal.end_date < goal.last_update) and (goal.state == 'failed'):
                    goal.color = 2
                elif (goal.end_date < goal.last_update) and (goal.state == 'reached'):
                    goal.color = 5
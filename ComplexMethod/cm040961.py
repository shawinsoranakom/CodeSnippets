def should_throttle(self, action):
        if (
            not config.DYNAMODB_READ_ERROR_PROBABILITY
            and not config.DYNAMODB_ERROR_PROBABILITY
            and not config.DYNAMODB_WRITE_ERROR_PROBABILITY
        ):
            # early exit so we don't need to call random()
            return False

        rand = random.random()
        if rand < config.DYNAMODB_READ_ERROR_PROBABILITY and self.action_should_throttle(
            action, READ_THROTTLED_ACTIONS
        ):
            return True
        elif rand < config.DYNAMODB_WRITE_ERROR_PROBABILITY and self.action_should_throttle(
            action, WRITE_THROTTLED_ACTIONS
        ):
            return True
        elif rand < config.DYNAMODB_ERROR_PROBABILITY and self.action_should_throttle(
            action, THROTTLED_ACTIONS
        ):
            return True
        return False
def lock_wait():
            # timeout after ~0.5 seconds
            for i in range(20):
                time.sleep(0.025)
                if lock_status["has_grabbed_lock"]:
                    return True
            return False
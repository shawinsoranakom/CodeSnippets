def birthday_sleep():
            lock_status["has_grabbed_lock"] = True
            time.sleep(0.5)
            return date(1940, 10, 10)
def birthday_yield():
            # At this point the row should be locked as create or update
            # defaults are only called once the SELECT FOR UPDATE is issued.
            locked_for_update.set()
            # Yield back the execution to the main thread until it allows
            # save() to proceed.
            save_allowed.clear()
            return date(1940, 10, 10)
def wait_for_allowed_save(*args, **kwargs):
            wait_or_fail(save_allowed, "Test took too long to allow save")
            return person_save(*args, **kwargs)
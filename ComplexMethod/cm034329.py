def wait_import_task(self, task_url, timeout=0):
        """
        Waits until the import process on the Galaxy server has completed or the timeout is reached.

        :param task_id: The id of the import task to wait for. This can be parsed out of the return
            value for GalaxyAPI.publish_collection.
        :param timeout: The timeout in seconds, 0 is no timeout.
        """
        state = 'waiting'
        data = None

        display.display("Waiting until Galaxy import task %s has completed" % task_url)
        start = time.time()
        wait = C.GALAXY_COLLECTION_IMPORT_POLL_INTERVAL

        while timeout == 0 or (time.time() - start) < timeout:
            try:
                data = self._call_galaxy(task_url, method='GET', auth_required=True,
                                         error_context_msg='Error when getting import task results at %s' % task_url)
            except GalaxyError as e:
                if e.http_code != 404:
                    raise
                # The import job may not have started, and as such, the task url may not yet exist
                display.vvv('Galaxy import process has not started, wait %s seconds before trying again' % wait)
                time.sleep(wait)
                continue

            state = data.get('state', 'waiting')

            if data.get('finished_at', None):
                break

            display.vvv('Galaxy import process has a status of %s, wait %d seconds before trying again'
                        % (state, wait))
            time.sleep(wait)

            # poor man's exponential backoff algo so we don't flood the Galaxy API, cap at 30 seconds.
            wait = min(30, wait * C.GALAXY_COLLECTION_IMPORT_POLL_FACTOR)
        if state == 'waiting':
            raise AnsibleError("Timeout while waiting for the Galaxy import process to finish, check progress at '%s'"
                               % to_native(task_url))

        for message in data.get('messages', []):
            level = message['level']
            if level.lower() == 'error':
                display.error("Galaxy import error message: %s" % message['message'])
            elif level.lower() == 'warning':
                display.warning("Galaxy import warning message: %s" % message['message'])
            else:
                display.vvv("Galaxy import message: %s - %s" % (level, message['message']))

        if state == 'failed':
            code = to_native(data['error'].get('code', 'UNKNOWN'))
            description = to_native(
                data['error'].get('description', "Unknown error, see %s for more details" % task_url))
            raise AnsibleError("Galaxy import process failed: %s (Code: %s)" % (description, code))
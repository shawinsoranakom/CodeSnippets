def _update_status(self, progress_percent=None, estimated_time_remaining=None, metrics=None, force=False):
        """Send progress update to Kubeflow Trainer controller."""
        import json
        import time
        import urllib.request
        from datetime import datetime, timezone

        try:
            url = os.environ.get(self._ENV_SERVER_URL)
            if not url:
                return False

            now = time.monotonic()
            if not force and (now - self._last_update_time) < self._MIN_UPDATE_INTERVAL:
                return False
            self._last_update_time = now

            token = self._get_token()
            if not token:
                return False

            trainer_status = {"lastUpdatedTime": datetime.now(timezone.utc).isoformat()}

            if progress_percent is not None:
                trainer_status["progressPercentage"] = max(0, min(100, progress_percent))

            if estimated_time_remaining is not None:
                trainer_status["estimatedRemainingSeconds"] = max(0, int(estimated_time_remaining))

            if metrics:
                trainer_status["metrics"] = [{"name": str(k), "value": str(v)} for k, v in metrics.items()]

            data = json.dumps({"trainerStatus": trainer_status}).encode("utf-8")
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5, context=self._get_ssl_context()) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug(f"[Kubeflow] Failed to update status: {e}")
            return False
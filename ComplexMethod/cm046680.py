def _cleanup_audio_artifacts(self):
        """Remove sys.path entries and sys.modules from previous audio preprocessing.

        After audio training, cloned repo dirs (OuteTTS, Spark-TTS) remain on
        sys.path and heavy audio modules (snac, whisper, sparktts, outetts) stay
        in sys.modules. When the next training run calls dataset.map(num_proc=N),
        forked child processes inherit this stale state and deadlock.
        """
        import sys as _sys

        # Remove cloned audio repo paths from sys.path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        audio_paths = [
            os.path.join(base_dir, "inference", "OuteTTS"),  # DAC/OuteTTS
        ]
        # Spark-TTS path is relative to the downloaded repo
        if self._spark_tts_repo_dir:
            spark_code_dir = os.path.join(
                os.path.dirname(self._spark_tts_repo_dir), "Spark-TTS"
            )
            audio_paths.append(spark_code_dir)

        removed_paths = []
        for path in audio_paths:
            if path in _sys.path:
                _sys.path.remove(path)
                removed_paths.append(path)

        # Remove stale audio modules from sys.modules
        prefixes = ("snac", "whisper", "sparktts", "outetts")
        removed_modules = [key for key in _sys.modules if key.startswith(prefixes)]
        for key in removed_modules:
            del _sys.modules[key]

        if removed_paths or removed_modules:
            logger.info(
                f"Cleaned up audio artifacts: {len(removed_paths)} paths, "
                f"{len(removed_modules)} modules\n"
            )
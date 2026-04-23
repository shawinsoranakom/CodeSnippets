def _run_transcription_job(self, args: tuple[TranscribeStore, str]) -> None:
        store, job_name = args

        job = store.transcription_jobs[job_name]
        job["StartTime"] = datetime.datetime.utcnow()
        job["TranscriptionJobStatus"] = TranscriptionJobStatus.IN_PROGRESS

        failure_reason = None

        try:
            LOG.debug("Starting transcription: %s", job_name)

            # Get file from S3
            file_path = new_tmp_file()
            s3_client = connect_to().s3
            s3_path: str = job["Media"]["MediaFileUri"]  # type: ignore[index,assignment]
            bucket, _, key = s3_path.removeprefix("s3://").partition("/")
            s3_client.download_file(Bucket=bucket, Key=key, Filename=file_path)

            ffmpeg_package.install()
            ffmpeg_bin = ffmpeg_package.get_installer().get_ffmpeg_path()
            ffprobe_bin = ffmpeg_package.get_installer().get_ffprobe_path()

            LOG.debug("Determining media format")
            # TODO set correct failure_reason if ffprobe execution fails
            ffprobe_output = json.loads(
                run(  # type: ignore[arg-type]
                    f"{ffprobe_bin} -show_streams -show_format -print_format json -hide_banner -v error {file_path}"
                )
            )
            format = ffprobe_output["format"]["format_name"]
            LOG.debug("Media format detected as: %s", format)
            job["MediaFormat"] = SUPPORTED_FORMAT_NAMES[format]
            duration = ffprobe_output["format"]["duration"]

            if float(duration) > MAX_AUDIO_DURATION_SECONDS:
                failure_reason = "Invalid file size: file size too large. Maximum audio duration is 4.000000 hours.Check the length of the file and try your request again."
                raise RuntimeError()

            # Determine the sample rate of input audio if possible
            for stream in ffprobe_output["streams"]:
                if stream["codec_type"] == "audio":
                    job["MediaSampleRateHertz"] = int(stream["sample_rate"])

            if format in SUPPORTED_FORMAT_NAMES:
                wav_path = new_tmp_file(suffix=".wav")
                LOG.debug("Transcoding media to wav")
                # TODO set correct failure_reason if ffmpeg execution fails
                run(
                    f"{ffmpeg_bin} -y -nostdin -loglevel quiet -i '{file_path}' -ar 16000 -ac 1 '{wav_path}'"
                )
            else:
                failure_reason = f"Unsupported media format: {format}"
                raise RuntimeError()

            # Check if file is valid wav
            audio = wave.open(wav_path, "rb")
            if (
                audio.getnchannels() != 1
                or audio.getsampwidth() != 2
                or audio.getcomptype() != "NONE"
            ):
                # Fail job
                failure_reason = (
                    "Audio file must be mono PCM WAV format. Transcoding may have failed. "
                )
                raise RuntimeError()

            # Prepare transcriber
            language_code: str = job["LanguageCode"]  # type: ignore[assignment]
            model_name = LANGUAGE_MODELS[language_code]  # type: ignore[index]
            self._setup_vosk()
            model_path = self.download_model(model_name)
            from vosk import KaldiRecognizer, Model  # noqa

            model = Model(model_path=model_path, model_name=model_name)

            tc = KaldiRecognizer(model, audio.getframerate())
            tc.SetWords(True)
            tc.SetPartialWords(True)

            # Start transcription
            while True:
                data = audio.readframes(4000)
                if len(data) == 0:
                    break
                tc.AcceptWaveform(data)

            tc_result = json.loads(tc.FinalResult())

            # Convert to AWS format
            items = []
            for unigram in tc_result["result"]:
                items.append(
                    {
                        "start_time": unigram["start"],
                        "end_time": unigram["end"],
                        "type": "pronunciation",
                        "alternatives": [
                            {
                                "confidence": unigram["conf"],
                                "content": unigram["word"],
                            }
                        ],
                    }
                )
            output = {
                "jobName": job_name,
                "status": TranscriptionJobStatus.COMPLETED,
                "results": {
                    "transcripts": [
                        {
                            "transcript": tc_result["text"],
                        }
                    ],
                    "items": items,
                },
            }

            # Save to S3
            output_s3_path: str = job["Transcript"]["TranscriptFileUri"]  # type: ignore[index,assignment]
            output_bucket, output_key = get_bucket_and_key_from_presign_url(output_s3_path)
            s3_client.put_object(Bucket=output_bucket, Key=output_key, Body=json.dumps(output))

            # Update job details
            job["CompletionTime"] = datetime.datetime.utcnow()
            job["TranscriptionJobStatus"] = TranscriptionJobStatus.COMPLETED
            job["MediaFormat"] = MediaFormat.wav

            LOG.info("Transcription job completed: %s", job_name)

        except Exception as exc:
            job["FailureReason"] = failure_reason or str(exc)
            job["TranscriptionJobStatus"] = TranscriptionJobStatus.FAILED

            LOG.error(
                "Transcription job %s failed: %s",
                job_name,
                job["FailureReason"],
                exc_info=LOG.isEnabledFor(logging.DEBUG),
            )
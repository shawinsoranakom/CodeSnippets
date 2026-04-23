def audio_convertion_thread(self, uuid):
        # 在一个异步线程中采集音频
        import nls  # pip install git+https://github.com/aliyun/alibabacloud-nls-python-sdk.git
        import tempfile
        from scipy import io
        from toolbox import get_conf
        from .audio_io import change_sample_rate
        from .audio_io import RealtimeAudioDistribution
        NEW_SAMPLERATE = 16000
        rad = RealtimeAudioDistribution()
        rad.clean_up()
        temp_folder = tempfile.gettempdir()
        TOKEN, APPKEY = get_conf('ALIYUN_TOKEN', 'ALIYUN_APPKEY')
        if len(TOKEN) == 0:
            TOKEN = self.get_token()
        self.aliyun_service_ok = True
        URL="wss://nls-gateway.aliyuncs.com/ws/v1"
        sr = nls.NlsSpeechTranscriber(
                    url=URL,
                    token=TOKEN,
                    appkey=APPKEY,
                    on_sentence_begin=self.test_on_sentence_begin,
                    on_sentence_end=self.test_on_sentence_end,
                    on_start=self.test_on_start,
                    on_result_changed=self.test_on_result_chg,
                    on_completed=self.test_on_completed,
                    on_error=self.test_on_error,
                    on_close=self.test_on_close,
                    callback_args=[uuid.hex]
                )
        timeout_limit_second = 20
        r = sr.start(aformat="pcm",
                timeout=timeout_limit_second,
                enable_intermediate_result=True,
                enable_punctuation_prediction=True,
                enable_inverse_text_normalization=True)

        import webrtcvad
        vad = webrtcvad.Vad()
        vad.set_mode(1)

        is_previous_frame_transmitted = False   # 上一帧是否有人说话
        previous_frame_data = None
        echo_cnt = 0        # 在没有声音之后，继续向服务器发送n次音频数据
        echo_cnt_max = 4   # 在没有声音之后，继续向服务器发送n次音频数据
        keep_alive_last_send_time = time.time()
        while not self.stop:
            # time.sleep(self.capture_interval)
            audio = rad.read(uuid.hex)
            if audio is not None:
                # convert to pcm file
                temp_file = f'{temp_folder}/{uuid.hex}.pcm' #
                dsdata = change_sample_rate(audio, rad.rate, NEW_SAMPLERATE) # 48000 --> 16000
                write_numpy_to_wave(temp_file, NEW_SAMPLERATE, dsdata)
                # read pcm binary
                with open(temp_file, "rb") as f: data = f.read()
                is_speaking, info = is_speaker_speaking(vad, data, NEW_SAMPLERATE)

                if is_speaking or echo_cnt > 0:
                    # 如果话筒激活 / 如果处于回声收尾阶段
                    echo_cnt -= 1
                    if not is_previous_frame_transmitted:   # 上一帧没有人声，但是我们把上一帧同样加上
                        if previous_frame_data is not None: data = previous_frame_data + data
                    if is_speaking:
                        echo_cnt = echo_cnt_max
                    slices = zip(*(iter(data),) * 640)      # 640个字节为一组
                    for i in slices: sr.send_audio(bytes(i))
                    keep_alive_last_send_time = time.time()
                    is_previous_frame_transmitted = True
                else:
                    is_previous_frame_transmitted = False
                    echo_cnt = 0
                    # 保持链接激活，即使没有声音，也根据时间间隔，发送一些音频片段给服务器
                    if time.time() - keep_alive_last_send_time > timeout_limit_second/2:
                        slices = zip(*(iter(data),) * 640)    # 640个字节为一组
                        for i in slices: sr.send_audio(bytes(i))
                        keep_alive_last_send_time = time.time()
                        is_previous_frame_transmitted = True
                self.audio_shape = info
            else:
                time.sleep(0.1)

            if not self.aliyun_service_ok:
                self.stop = True
                self.stop_msg = 'Aliyun音频服务异常，请检查ALIYUN_TOKEN和ALIYUN_APPKEY是否过期。'
        r = sr.stop()
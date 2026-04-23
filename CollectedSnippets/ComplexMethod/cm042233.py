def run_step(self, msg: capnp._DynamicStructReader, frs: dict[str, FrameReader] | None) -> list[capnp._DynamicStructReader]:
    assert self.rc and self.pm and self.sockets and self.process.proc

    output_msgs = []
    end_of_cycle = True
    if self.cfg.should_recv_callback is not None:
      end_of_cycle = self.cfg.should_recv_callback(msg, self.cfg, self.cnt)

    self.msg_queue.append(msg)
    if end_of_cycle:
      with self.prefix, Timeout(self.cfg.timeout, error_msg=f"timed out testing process {repr(self.cfg.proc_name)}"):
        # call recv to let sub-sockets reconnect, after we know the process is ready
        if self.cnt == 0:
          for s in self.sockets:
            messaging.recv_one_or_none(s)

        # certain processes use drain_sock. need to cause empty recv to break from this loop
        trigger_empty_recv = False
        if self.cfg.main_pub and self.cfg.main_pub_drained:
          trigger_empty_recv = any(m.which() == self.cfg.main_pub for m in self.msg_queue)

        # get output msgs from previous inputs
        output_msgs = self.get_output_msgs(self.last_input_log_mono_time)

        for m in self.msg_queue:
          self.pm.send(m.which(), m.as_builder())
          self.last_input_log_mono_time = max(self.last_input_log_mono_time, m.logMonoTime)
          # send frames if needed
          if self.vipc_server is not None and m.which() in self.cfg.vision_pubs:
            camera_state = getattr(m, m.which())
            camera_meta = meta_from_camera_state(m.which())
            assert frs is not None
            img = frs[m.which()].get(camera_state.frameId)

            h, w = frs[m.which()].h, frs[m.which()].w
            stride, y_height, _, yuv_size = get_nv12_info(w, h)
            uv_offset = stride * y_height
            padded_img = np.zeros(((uv_offset //stride) + (h // 2), stride))
            padded_img[:h, :w] = img[:h * w].reshape((-1, w))
            padded_img[uv_offset // stride:uv_offset // stride + h // 2, :w] = img[h * w:].reshape((-1, w))
            img_bytes = np.zeros((yuv_size,), dtype=np.uint8)
            img_bytes[:padded_img.size] = padded_img.flatten()

            self.vipc_server.send(camera_meta.stream, img_bytes.tobytes(),
                                  camera_state.frameId, camera_state.timestampSof, camera_state.timestampEof)
        self.msg_queue = []

        self.rc.unlock_sockets()
        if trigger_empty_recv:
          self.rc.unlock_sockets()
        self.cnt += 1
    assert self.process.proc.is_alive()

    return output_msgs
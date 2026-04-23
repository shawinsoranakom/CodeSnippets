def decoder(addr, vipc_server, vst, nvidia, W, H, debug=False):
  sock_name = ENCODE_SOCKETS[vst]
  if debug:
    print(f"start decoder for {sock_name}, {W}x{H}")

  if nvidia:
    os.environ["NV_LOW_LATENCY"] = "3"    # both bLowLatency and CUVID_PKT_ENDOFPICTURE
    sys.path += os.environ["LD_LIBRARY_PATH"].split(":")
    import PyNvCodec as nvc

    nvDec = nvc.PyNvDecoder(W, H, nvc.PixelFormat.NV12, nvc.CudaVideoCodec.HEVC, 0)
    cc1 = nvc.ColorspaceConversionContext(nvc.ColorSpace.BT_709, nvc.ColorRange.JPEG)
    conv_yuv = nvc.PySurfaceConverter(W, H, nvc.PixelFormat.NV12, nvc.PixelFormat.YUV420, 0)
    nvDwn_yuv = nvc.PySurfaceDownloader(W, H, nvc.PixelFormat.YUV420, 0)
    img_yuv = np.ndarray((H*W//2*3), dtype=np.uint8)
  else:
    codec = av.CodecContext.create("hevc", "r")

  os.environ["ZMQ"] = "1"
  messaging.reset_context()
  sock = messaging.sub_sock(sock_name, None, addr=addr, conflate=False)
  cnt = 0
  last_idx = -1
  seen_iframe = False

  time_q = []
  while 1:
    msgs = messaging.drain_sock(sock, wait_for_one=True)
    for evt in msgs:
      evta = getattr(evt, evt.which())
      if debug and evta.idx.encodeId != 0 and evta.idx.encodeId != (last_idx+1):
        print("DROP PACKET!")
      last_idx = evta.idx.encodeId
      if not seen_iframe and not (evta.idx.flags & V4L2_BUF_FLAG_KEYFRAME):
        if debug:
          print("waiting for iframe")
        continue
      time_q.append(time.monotonic())
      network_latency = (int(time.time()*1e9) - evta.unixTimestampNanos)/1e6  # noqa: TID251
      frame_latency = ((evta.idx.timestampEof/1e9) - (evta.idx.timestampSof/1e9))*1000
      process_latency = ((evt.logMonoTime/1e9) - (evta.idx.timestampEof/1e9))*1000

      # put in header (first)
      if not seen_iframe:
        if nvidia:
          nvDec.DecodeSurfaceFromPacket(np.frombuffer(evta.header, dtype=np.uint8))
        else:
          codec.decode(av.packet.Packet(evta.header))
        seen_iframe = True

      if nvidia:
        rawSurface = nvDec.DecodeSurfaceFromPacket(np.frombuffer(evta.data, dtype=np.uint8))
        if rawSurface.Empty():
          if debug:
            print("DROP SURFACE")
          continue
        convSurface = conv_yuv.Execute(rawSurface, cc1)
        nvDwn_yuv.DownloadSingleSurface(convSurface, img_yuv)
      else:
        frames = codec.decode(av.packet.Packet(evta.data))
        if len(frames) == 0:
          if debug:
            print("DROP SURFACE")
          continue
        assert len(frames) == 1
        img_yuv = frames[0].to_ndarray(format=av.video.format.VideoFormat('yuv420p')).flatten()
        uv_offset = H*W
        y = img_yuv[:uv_offset]
        uv = img_yuv[uv_offset:].reshape(2, -1).ravel('F')
        img_yuv = np.hstack((y, uv))

      vipc_server.send(vst, img_yuv.data, cnt, int(time_q[0]*1e9), int(time.monotonic()*1e9))
      cnt += 1

      pc_latency = (time.monotonic()-time_q[0])*1000
      time_q = time_q[1:]
      if debug:
        print(f"{len(msgs):2d} {evta.idx.encodeId:4d} {evt.logMonoTime/1e9:.3f} {evta.idx.timestampEof/1e6:.3f} \
            roll {frame_latency:6.2f} ms latency {process_latency:6.2f} ms + {network_latency:6.2f} ms + {pc_latency:6.2f} ms \
            = {process_latency+network_latency+pc_latency:6.2f} ms", len(evta.data), sock_name)
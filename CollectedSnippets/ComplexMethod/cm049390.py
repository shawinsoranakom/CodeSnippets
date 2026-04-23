def send(self, msgs):
        """ Send and receive messages to/from the fiscal device over serial connection

        Generate the wrapped message from the msgs and send them to the device.
        The wrapping contains the <STX> (starting byte) <LEN> (length byte)
        and <NBL> (message number byte) at the start and two <CS> (checksum
        bytes), and the <ETX> line-feed byte at the end.
        :param msgs: A list of byte strings representing the <CMD> and <DATA>
                     components of the serial message.
        :return:     A list of the responses (if any) from the device. If the
                     response is an ack, it wont be part of this list.
        """

        with self._device_lock:
            replies = []
            for msg in msgs:
                self.message_number += 1
                core_message = struct.pack('BB%ds' % (len(msg)), len(msg) + 34, self.message_number + 32, msg)
                request = struct.pack('B%ds2sB' % (len(core_message)), STX, core_message, self.generate_checksum(core_message), ETX)
                time.sleep(self._protocol.commandDelay)
                self._connection.write(request)
                _logger.debug('Debug send request: %s', request)
                # If we know the expected output size, we can set the read
                # buffer to match the size of the output.
                output_size = COMMAND_OUTPUT_SIZE.get(msg[0])
                if output_size:
                    try:
                        response = self._connection.read(output_size)
                    except serial.serialutil.SerialTimeoutException:
                        _logger.exception('Timeout error while reading response to command %s', msg)
                        self.data['status'] = "Device timeout error"
                else:
                    time.sleep(self._protocol.measureDelay)
                    response = self._connection.read_all()
                _logger.debug('Debug send response: %s', response)
                if not response:
                    self.data['status'] = "No response"
                    _logger.error("Sent request: %s,\n Received no response", request)
                    self.abort_post()
                    break
                if response[0] == ACK:
                    # In the case where either byte is not 0x30, there has been an error
                    if response[2] != 0x30 or response[3] != 0x30:
                        self.data['status'] = response[2:4].decode('cp1251')
                        _logger.error(
                            "Sent request: %s,\n Received fiscal device error: %s \n Received command error: %s",
                            request, FD_ERRORS.get(response[2], 'Unknown fiscal device error'),
                            COMMAND_ERRORS.get(response[3], 'Unknown command error'),
                        )
                        self.abort_post()
                        break
                    replies.append('')
                elif response[0] == NACK:
                    self.data['status'] = "Received NACK"
                    _logger.error("Sent request: %s,\n Received NACK \x15", request)
                    self.abort_post()
                    break
                elif response[0] == 0x02:
                    self.data['status'] = "ok"
                    size = response[1] - 35
                    reply = response[4:4 + size]
                    replies.append(reply.decode('cp1251'))
        return {'replies': replies, 'status': self.data['status']}
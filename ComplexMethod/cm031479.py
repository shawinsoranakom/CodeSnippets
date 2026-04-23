def pollresponse(self, myseq, wait):
        """Handle messages received on the socket.

        Some messages received may be asynchronous 'call' or 'queue' requests,
        and some may be responses for other threads.

        'call' requests are passed to self.localcall() with the expectation of
        immediate execution, during which time the socket is not serviced.

        'queue' requests are used for tasks (which may block or hang) to be
        processed in a different thread.  These requests are fed into
        request_queue by self.localcall().  Responses to queued requests are
        taken from response_queue and sent across the link with the associated
        sequence numbers.  Messages in the queues are (sequence_number,
        request/response) tuples and code using this module removing messages
        from the request_queue is responsible for returning the correct
        sequence number in the response_queue.

        pollresponse() will loop until a response message with the myseq
        sequence number is received, and will save other responses in
        self.responses and notify the owning thread.

        """
        while True:
            # send queued response if there is one available
            try:
                qmsg = response_queue.get(0)
            except queue.Empty:
                pass
            else:
                seq, response = qmsg
                message = (seq, ('OK', response))
                self.putmessage(message)
            # poll for message on link
            try:
                message = self.pollmessage(wait)
                if message is None:  # socket not ready
                    return None
            except EOFError:
                self.handle_EOF()
                return None
            except AttributeError:
                return None
            seq, resq = message
            how = resq[0]
            self.debug("pollresponse:%d:myseq:%s" % (seq, myseq))
            # process or queue a request
            if how in ("CALL", "QUEUE"):
                self.debug("pollresponse:%d:localcall:call:" % seq)
                response = self.localcall(seq, resq)
                self.debug("pollresponse:%d:localcall:response:%s"
                           % (seq, response))
                if how == "CALL":
                    self.putmessage((seq, response))
                elif how == "QUEUE":
                    # don't acknowledge the 'queue' request!
                    pass
                continue
            # return if completed message transaction
            elif seq == myseq:
                return resq
            # must be a response for a different thread:
            else:
                cv = self.cvars.get(seq, None)
                # response involving unknown sequence number is discarded,
                # probably intended for prior incarnation of server
                if cv is not None:
                    cv.acquire()
                    self.responses[seq] = resq
                    cv.notify()
                    cv.release()
                continue
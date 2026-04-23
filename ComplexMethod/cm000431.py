async def connect(self):
        if self.is_connected and self._channel and not self._channel.is_closed:
            return

        if (
            self.is_connected
            and self._connection
            and (self._channel is None or self._channel.is_closed)
        ):
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=1)
            await self.declare_infrastructure()
            return

        self._connection = await aio_pika.connect_robust(
            host=self.host,
            port=self.port,
            login=self.username,
            password=self.password,
            virtualhost=self.config.vhost.lstrip("/"),
            blocked_connection_timeout=BLOCKED_CONNECTION_TIMEOUT,
            heartbeat=300,  # 5 minute timeout (heartbeats sent every 2.5 min)
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)

        await self.declare_infrastructure()
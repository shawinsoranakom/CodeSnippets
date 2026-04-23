def exec_in_container(
        self,
        container_name_or_id: str,
        command: list[str] | str,
        interactive=False,
        detach=False,
        env_vars: dict[str, str | None] | None = None,
        stdin: bytes | None = None,
        user: str | None = None,
        workdir: str | None = None,
    ) -> tuple[bytes, bytes]:
        LOG.debug("Executing command in container %s: %s", container_name_or_id, command)
        try:
            container: Container = self.client().containers.get(container_name_or_id)
            result = container.exec_run(
                cmd=command,
                environment=env_vars,
                user=user,
                detach=detach,
                stdin=interactive and bool(stdin),
                socket=interactive and bool(stdin),
                stdout=True,
                stderr=True,
                demux=True,
                workdir=workdir,
            )
            tty = False
            if interactive and stdin:  # result is a socket
                sock = result[1]
                sock = sock._sock if hasattr(sock, "_sock") else sock
                with sock:
                    try:
                        sock.sendall(stdin)
                        sock.shutdown(socket.SHUT_WR)
                        stdout, stderr = self._read_from_sock(sock, tty)
                        return stdout, stderr
                    except TimeoutError:
                        pass
            else:
                if detach:
                    return b"", b""
                return_code = result[0]
                if isinstance(result[1], bytes):
                    stdout = result[1]
                    stderr = b""
                else:
                    stdout, stderr = result[1]
                if return_code != 0:
                    raise ContainerException(
                        f"Exec command returned with exit code {return_code}", stdout, stderr
                    )
                return stdout, stderr
        except ContainerError:
            raise NoSuchContainer(container_name_or_id)
        except APIError as e:
            raise ContainerException() from e
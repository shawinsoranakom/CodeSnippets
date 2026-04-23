async def add_instance_endpoint(self, request: Request):
        try:
            data = await request.json()
            logger.warning(str(data))
            instance_type = data.get("type")
            instance = data.get("instance")
            if instance_type not in ["prefill", "decode"]:
                raise HTTPException(status_code=400, detail="Invalid instance type.")
            if not instance or ":" not in instance:
                raise HTTPException(status_code=400, detail="Invalid instance format.")
            host, port_str = instance.split(":")
            try:
                if host != "localhost":
                    ipaddress.ip_address(host)
                port = int(port_str)
                if not (0 < port < 65536):
                    raise HTTPException(status_code=400, detail="Invalid port number.")
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail="Invalid instance address."
                ) from e

            is_valid = await self.validate_instance(instance)
            if not is_valid:
                raise HTTPException(
                    status_code=400, detail="Instance validation failed."
                )

            if instance_type == "prefill":
                if instance not in self.prefill_instances:
                    self.prefill_instances.append(instance)
                    self.prefill_cycler = itertools.cycle(self.prefill_instances)
                else:
                    raise HTTPException(
                        status_code=400, detail="Instance already exists."
                    )
            else:
                if instance not in self.decode_instances:
                    self.decode_instances.append(instance)
                    self.decode_cycler = itertools.cycle(self.decode_instances)
                else:
                    raise HTTPException(
                        status_code=400, detail="Instance already exists."
                    )

            return JSONResponse(
                content={"message": f"Added {instance} to {instance_type}_instances."}
            )
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error("Error in add_instance_endpoint: %s", str(e))
            raise HTTPException(status_code=500, detail=str(e)) from e
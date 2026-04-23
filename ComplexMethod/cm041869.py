def find(self, description, screenshot=None):
        if description.startswith('"') and description.endswith('"'):
            return self.find_text(description.strip('"'), screenshot)
        else:
            try:
                if self.computer.debug:
                    print("DEBUG MODE ON")
                    print("NUM HASHES:", len(self._hashes))
                else:
                    message = format_to_recipient(
                        "Locating this icon will take ~15 seconds. Subsequent icons should be found more quickly.",
                        recipient="user",
                    )
                    print(message)

                if len(self._hashes) > 5000:
                    self._hashes = dict(list(self._hashes.items())[-5000:])

                from .point.point import point

                result = point(
                    description, screenshot, self.computer.debug, self._hashes
                )

                return result
            except:
                if self.computer.debug:
                    # We want to know these bugs lmao
                    raise
                if self.computer.offline:
                    raise
                message = format_to_recipient(
                    "Locating this icon will take ~30 seconds. We're working on speeding this up.",
                    recipient="user",
                )
                print(message)

                # Take a screenshot
                if screenshot == None:
                    screenshot = self.screenshot(show=False)

                # Downscale the screenshot to 1920x1080
                screenshot = screenshot.resize((1920, 1080))

                # Convert the screenshot to base64
                buffered = BytesIO()
                screenshot.save(buffered, format="PNG")
                screenshot_base64 = base64.b64encode(buffered.getvalue()).decode()

                try:
                    response = requests.post(
                        f'{self.computer.api_base.strip("/")}/point/',
                        json={"query": description, "base64": screenshot_base64},
                    )
                    return response.json()
                except Exception as e:
                    raise Exception(
                        str(e)
                        + "\n\nIcon locating API not available, or we were unable to find the icon. Please try another method to find this icon."
                    )
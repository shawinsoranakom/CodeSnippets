def _run(self, history, **kwargs):
        if self.check_if_canceled("Qweather processing"):
            return

        ans = self.get_input()
        ans = "".join(ans["content"]) if "content" in ans else ""
        if not ans:
            return QWeather.be_output("")

        try:
            if self.check_if_canceled("Qweather processing"):
                return

            response = requests.get(
                url="https://geoapi.qweather.com/v2/city/lookup?location=" + ans + "&key=" + self._param.web_apikey).json()
            if response["code"] == "200":
                location_id = response["location"][0]["id"]
            else:
                return QWeather.be_output("**Error**" + self._param.error_code[response["code"]])

            if self.check_if_canceled("Qweather processing"):
                return

            base_url = "https://api.qweather.com/v7/" if self._param.user_type == 'paid' else "https://devapi.qweather.com/v7/"

            if self._param.type == "weather":
                url = base_url + "weather/" + self._param.time_period + "?location=" + location_id + "&key=" + self._param.web_apikey + "&lang=" + self._param.lang
                response = requests.get(url=url).json()
                if self.check_if_canceled("Qweather processing"):
                    return
                if response["code"] == "200":
                    if self._param.time_period == "now":
                        return QWeather.be_output(str(response["now"]))
                    else:
                        qweather_res = [{"content": str(i) + "\n"} for i in response["daily"]]
                        if self.check_if_canceled("Qweather processing"):
                            return
                        if not qweather_res:
                            return QWeather.be_output("")

                        df = pd.DataFrame(qweather_res)
                        return df
                else:
                    return QWeather.be_output("**Error**" + self._param.error_code[response["code"]])

            elif self._param.type == "indices":
                url = base_url + "indices/1d?type=0&location=" + location_id + "&key=" + self._param.web_apikey + "&lang=" + self._param.lang
                response = requests.get(url=url).json()
                if self.check_if_canceled("Qweather processing"):
                    return
                if response["code"] == "200":
                    indices_res = response["daily"][0]["date"] + "\n" + "\n".join(
                        [i["name"] + ": " + i["category"] + ", " + i["text"] for i in response["daily"]])
                    return QWeather.be_output(indices_res)

                else:
                    return QWeather.be_output("**Error**" + self._param.error_code[response["code"]])

            elif self._param.type == "airquality":
                url = base_url + "air/now?location=" + location_id + "&key=" + self._param.web_apikey + "&lang=" + self._param.lang
                response = requests.get(url=url).json()
                if self.check_if_canceled("Qweather processing"):
                    return
                if response["code"] == "200":
                    return QWeather.be_output(str(response["now"]))
                else:
                    return QWeather.be_output("**Error**" + self._param.error_code[response["code"]])
        except Exception as e:
            if self.check_if_canceled("Qweather processing"):
                return
            return QWeather.be_output("**Error**" + str(e))
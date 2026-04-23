def _run(self, history, **kwargs):
        if self.check_if_canceled("Jin10 processing"):
            return

        ans = self.get_input()
        ans = " - ".join(ans["content"]) if "content" in ans else ""
        if not ans:
            return Jin10.be_output("")

        jin10_res = []
        headers = {'secret-key': self._param.secret_key}
        try:
            if self.check_if_canceled("Jin10 processing"):
                return

            if self._param.type == "flash":
                params = {
                    'category': self._param.flash_type,
                    'contain': self._param.contain,
                    'filter': self._param.filter
                }
                response = requests.get(
                    url='https://open-data-api.jin10.com/data-api/flash?category=' + self._param.flash_type,
                    headers=headers, data=json.dumps(params))
                response = response.json()
                for i in response['data']:
                    if self.check_if_canceled("Jin10 processing"):
                        return
                    jin10_res.append({"content": i['data']['content']})
            if self._param.type == "calendar":
                params = {
                    'category': self._param.calendar_type
                }
                response = requests.get(
                    url='https://open-data-api.jin10.com/data-api/calendar/' + self._param.calendar_datatype + '?category=' + self._param.calendar_type,
                    headers=headers, data=json.dumps(params))

                response = response.json()
                if self.check_if_canceled("Jin10 processing"):
                    return
                jin10_res.append({"content": pd.DataFrame(response['data']).to_markdown()})
            if self._param.type == "symbols":
                params = {
                    'type': self._param.symbols_type
                }
                if self._param.symbols_datatype == "quotes":
                    params['codes'] = 'BTCUSD'
                response = requests.get(
                    url='https://open-data-api.jin10.com/data-api/' + self._param.symbols_datatype + '?type=' + self._param.symbols_type,
                    headers=headers, data=json.dumps(params))
                response = response.json()
                if self.check_if_canceled("Jin10 processing"):
                    return
                if self._param.symbols_datatype == "symbols":
                    for i in response['data']:
                        if self.check_if_canceled("Jin10 processing"):
                            return
                        i['Commodity Code'] = i['c']
                        i['Stock Exchange'] = i['e']
                        i['Commodity Name'] = i['n']
                        i['Commodity Type'] = i['t']
                        del i['c'], i['e'], i['n'], i['t']
                if self._param.symbols_datatype == "quotes":
                    for i in response['data']:
                        if self.check_if_canceled("Jin10 processing"):
                            return
                        i['Selling Price'] = i['a']
                        i['Buying Price'] = i['b']
                        i['Commodity Code'] = i['c']
                        i['Stock Exchange'] = i['e']
                        i['Highest Price'] = i['h']
                        i['Yesterday’s Closing Price'] = i['hc']
                        i['Lowest Price'] = i['l']
                        i['Opening Price'] = i['o']
                        i['Latest Price'] = i['p']
                        i['Market Quote Time'] = i['t']
                        del i['a'], i['b'], i['c'], i['e'], i['h'], i['hc'], i['l'], i['o'], i['p'], i['t']
                jin10_res.append({"content": pd.DataFrame(response['data']).to_markdown()})
            if self._param.type == "news":
                params = {
                    'contain': self._param.contain,
                    'filter': self._param.filter
                }
                response = requests.get(
                    url='https://open-data-api.jin10.com/data-api/news',
                    headers=headers, data=json.dumps(params))
                response = response.json()
                if self.check_if_canceled("Jin10 processing"):
                    return
                jin10_res.append({"content": pd.DataFrame(response['data']).to_markdown()})
        except Exception as e:
            if self.check_if_canceled("Jin10 processing"):
                return
            return Jin10.be_output("**ERROR**: " + str(e))

        if not jin10_res:
            return Jin10.be_output("")

        return pd.DataFrame(jin10_res)
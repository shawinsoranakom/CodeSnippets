def generate(self,
               browsers: Optional[List[str]] = None,
               os: Optional[Union[str, List[str]]] = None,
               min_version: float = 0.0,
               platforms: Optional[Union[str, List[str]]] = None, 
               pct_threshold: Optional[float] = None,
               fallback: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36") -> Dict:

       if not self.agents:
           self._fetch_agents()

       filtered_agents = self.agents

       if pct_threshold:
           filtered_agents = [a for a in filtered_agents if a['pct'] >= pct_threshold]

       if browsers:
           filtered_agents = [a for a in filtered_agents 
                            if any(b.lower() in a['ua'].lower() for b in browsers)]

       if os:
           os_list = [os] if isinstance(os, str) else os
           filtered_agents = [a for a in filtered_agents 
                            if any(o.lower() in a['ua'].lower() for o in os_list)]

       if platforms:
           platform_list = [platforms] if isinstance(platforms, str) else platforms
           filtered_agents = [a for a in filtered_agents 
                            if any(p.lower() in a['ua'].lower() for p in platform_list)]

       return filtered_agents[0] if filtered_agents else {'ua': fallback, 'pct': 0}
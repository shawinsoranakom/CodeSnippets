def p(self, stream_id=None):
        maybe_print("site:                %s" % self.__class__.name)
        maybe_print("title:               %s" % self.title)
        if stream_id:
            # Print the stream
            print("stream:")
            self.p_stream(stream_id)

        elif stream_id is None:
            # Print stream with best quality
            print("stream:              # Best quality")
            stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']
            self.p_stream(stream_id)

        elif stream_id == []:
            print("streams:             # Available quality and codecs")
            # Print DASH streams
            if self.dash_streams:
                print("    [ DASH ] %s" % ('_' * 36))
                itags = sorted(self.dash_streams,
                               key=lambda i: -self.dash_streams[i]['size'])
                for stream in itags:
                    self.p_stream(stream)
            # Print all other available streams
            if self.streams_sorted:
                print("    [ DEFAULT ] %s" % ('_' * 33))
                for stream in self.streams_sorted:
                    self.p_stream(stream['id'] if 'id' in stream else stream['itag'])

        if self.audiolang:
            print("audio-languages:")
            for i in self.audiolang:
                print("    - lang:          {}".format(i['lang']))
                print("      download-url:  {}\n".format(i['url']))

        sys.stdout.flush()
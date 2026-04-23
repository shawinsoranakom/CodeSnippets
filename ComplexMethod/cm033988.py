def _winrm_get_raw_command_output(
        self,
        protocol: winrm.Protocol,
        shell_id: str,
        command_id: str,
    ) -> tuple[bytes, bytes, int, bool]:
        rq = {'env:Envelope': protocol._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive',
            shell_id=shell_id)}

        stream = rq['env:Envelope'].setdefault('env:Body', {}).setdefault('rsp:Receive', {})\
            .setdefault('rsp:DesiredStream', {})
        stream['@CommandId'] = command_id
        stream['#text'] = 'stdout stderr'

        res = protocol.send_message(xmltodict.unparse(rq))
        root = ET.fromstring(res)
        stream_nodes = [
            node for node in root.findall('.//*')
            if node.tag.endswith('Stream')]
        stdout = []
        stderr = []
        return_code = -1
        for stream_node in stream_nodes:
            if not stream_node.text:
                continue
            if stream_node.attrib['Name'] == 'stdout':
                stdout.append(base64.b64decode(stream_node.text.encode('ascii')))
            elif stream_node.attrib['Name'] == 'stderr':
                stderr.append(base64.b64decode(stream_node.text.encode('ascii')))

        command_done = len([
            node for node in root.findall('.//*')
            if node.get('State', '').endswith('CommandState/Done')]) == 1
        if command_done:
            return_code = int(
                next(node for node in root.findall('.//*')
                     if node.tag.endswith('ExitCode')).text)

        return b"".join(stdout), b"".join(stderr), return_code, command_done
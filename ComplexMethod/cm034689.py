def _find_session_in_har_files(cls) -> Optional[dict]:
        """
        Search for valid session data in HAR files.

        Returns:
            Optional[dict]: Session data if found, None otherwise
        """
        try:
            for file in get_har_files():
                try:
                    with open(file, 'rb') as f:
                        har_data = json.load(f)

                    for entry in har_data['log']['entries']:
                        # Only look at blackbox API responses
                        if 'blackbox.ai/api' in entry['request']['url']:
                            # Look for a response that has the right structure
                            if 'response' in entry and 'content' in entry['response']:
                                content = entry['response']['content']
                                # Look for both regular and Google auth session formats
                                if ('text' in content and 
                                    isinstance(content['text'], str) and 
                                    '"user"' in content['text'] and 
                                    '"email"' in content['text'] and
                                    '"expires"' in content['text']):
                                    try:
                                        # Remove any HTML or other non-JSON content
                                        text = content['text'].strip()
                                        if text.startswith('{') and text.endswith('}'):
                                            # Replace escaped quotes
                                            text = text.replace('\\"', '"')
                                            har_session = json.loads(text)

                                            # Check if this is a valid session object
                                            if (isinstance(har_session, dict) and 
                                                'user' in har_session and 
                                                'email' in har_session['user'] and
                                                'expires' in har_session):

                                                debug.log(f"BlackboxPro: Found session in HAR file: {file}")
                                                return har_session
                                    except json.JSONDecodeError as e:
                                        # Only print error for entries that truly look like session data
                                        if ('"user"' in content['text'] and 
                                            '"email"' in content['text']):
                                            debug.log(f"BlackboxPro: Error parsing likely session data: {e}")
                except Exception as e:
                    debug.log(f"BlackboxPro: Error reading HAR file {file}: {e}")
            return None
        except NoValidHarFileError:
            pass
        except Exception as e:
            debug.log(f"BlackboxPro: Error searching HAR files: {e}")
            return None
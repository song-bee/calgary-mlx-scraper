"""Debug utilities for the scraper"""

import json
from typing import Dict, Any
from requests import Response
from .utils import getch

class DebugHelper:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.pause_enabled = True
        self.debug_keys = ['p', 'c', 'q']

    def print_request_info(self, method: str, url: str, headers: Dict, payload: Dict):
        """Print detailed request information"""
        if not self.debug_mode:
            return

        print("\n" + "="*80)
        print(f"REQUEST: {method} {url}")
        print("\nHEADERS:")
        print(json.dumps(headers, indent=2))
        print("\nPAYLOAD:")
        print(json.dumps(payload, indent=2))
        print("="*80 + "\n")

    def print_response_info(self, response: Response):
        """Print detailed response information"""
        if not self.debug_mode:
            return

        print("\n" + "="*80)
        print(f"Request Cookies: {response.request._cookies}")
        for cookie in response.request._cookies:
            print(f'{cookie.name}: {cookie.value}')

        print(response.request.body)

        print("RESPONSE:")
        print(f"Status Code: {response.status_code}")
        print("\nResponse Headers:")
        print(json.dumps(dict(response.headers), indent=2))
        #print(response.request.headers)
        print("\nResponse Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(response.text)
        print("="*80 + "\n")

        getch()        

    def debug_pause(self, context: str = "") -> bool:
        """Pause execution and wait for user input"""
        if not self.debug_mode or not self.pause_enabled:
            return True

        getch()        
        return True

        while True:
            user_input = input(
                f"\nDEBUG PAUSE {context}\n"
                f"Press 'p' to proceed with this request\n"
                f"Press 'c' to continue without further pauses\n"
                f"Press 'q' to quit\n"
                f"Choice: "
            ).lower()

            if user_input in self.debug_keys:
                if user_input == 'c':
                    self.pause_enabled = False
                    return True
                elif user_input == 'q':
                    return False
                else:  # 'p'
                    return True

            print("Invalid input! Please try again.") 
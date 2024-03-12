#!/usr/bin/env python
# -*- coding: utf-8 -*-

from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import os
from pyotp import TOTP
from dotenv import load_dotenv

class AngelBrokingAPI:
    def __init__(self):
        load_dotenv()
        self.AngelTotptoken = os.environ.get("TOTP_QR")
        self.AngelApiKey = os.environ.get("API_KEY")
        self.AngelClientId = os.environ.get("CLIENT_ID")
        self.AngelPassword = os.environ.get("PASSWORD")
        self.TOTP = TOTP(self.AngelTotptoken)
        self.smartApi = None
        self.session_data = None
        # self.init()
        # self.get_session()

    def init(self):
        if self.smartApi is None:
            self.smartApi = SmartConnect(api_key=self.AngelApiKey)
        self.get_session()
        return self.smartApi
     
    def get_session(self):
        if self.smartApi is None:
            self.init()

        if self.session_data is None:
            try:
                self.session_data = self.smartApi.generateSession(self.AngelClientId, self.AngelPassword, self.TOTP.now())
            except Exception as e:
                # Handle the exception as needed
                print("Session generation failed:", str(e))

        return self.session_data

    def get_feed_token(self):
        if self.smartApi is None:
            self.init()
        
        feed_token = self.smartApi.getfeedToken()
        return feed_token

    def create_websocket(self):
        session_data = self.get_session()
        feed_token = self.get_feed_token()
        if session_data:
            jwt_token = session_data.get("data", {}).get("jwtToken")
            if jwt_token:
                websocket = SmartWebSocketV2(jwt_token, self.AngelClientId, self.AngelPassword, feed_token)
                return websocket
            else:
                print("JWT token not found in session data.")
        else:
            print("Session data not available. Please call get_session first.")


# Usage
# api = AngelBrokingAPI()
# session_data = api.get_session()
# feed_token = api.get_feed_token()
# websocket = api.create_websocket()
# response = api.smartApi.orderBook()
# response = response['data']
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from urllib.parse import urlencode


class Session:
    """
    This class handles the Session to an arubaos8 device (Controller or mobility conductor)
    If a path for a cache-location is provided, it can also cache the session to lower the amount of logins.
    It provides get, put and post methods for sending commands.
    """
    session_timeout = 900

    def __init__(self, host, username, password, cachepath=None, verify_tls=False, port=4343):
        self._sessionid = None
        self.host = host
        self.username = username
        self.password = password
        self.verify_tls = verify_tls
        self.use_cache = cachepath is not None
        self.is_cached = False
        self.s = requests.session()
        self.base_url = f"https://{host}:{port}/v1/"
        self._cache_path = f"{cachepath}/aossession-{self.host}.json" if cachepath is not None else ""

        #check for cached login first, if not present,
        if self.use_cache:
            self._load_cache()

        if self._sessionid is None:
            self.login()

    def _load_cache(self):
        try:
            with open(self._cache_path, "r") as fp:
                ca = json.load(fp)
                if ('sessionid' and 'login_time') in ca and (time.time() - ca['login_time']) < self.session_timeout:
                    self._sessionid = ca['sessionid']
                    self.s.cookies.set_cookie(requests.cookies.create_cookie(name='SESSION', value=self._sessionid))
                    self.is_cached = True
                    self._last_rtime = ca['login_time']
                    return True
        except:
            # if cache file does not exist, or is not readable, just return false and proceed to login.
            pass
        return False

    def _save_cache(self):
        if self._sessionid is not None:
            with open(self._cache_path, 'wt') as file:
                json.dump({'sessionid': self.s.cookies.get("SESSION"), 'login_time': time.time()}, file)
                return True
        return False

    def _delete_cache(self):
        with open(self._cache_path, 'wt') as file:
            json.dump({}, file)
            return True

    def login(self):
        url = f"{self.base_url}api/login"
        login_str = f"username={self.username}&password={self.password}"

        r = self.s.post(
            url=url,
            data=login_str,
            headers={'Content-Type': 'application/json'},
            verify=self.verify_tls
        )

        if r.status_code != 200:
            print('Status:', r.status_code, 'Headers:', r.headers,
                  'Error Response:', r.reason)
            self._sessionid = None
            return False

        self._sessionid = r.json()["_global_result"]['UIDARUBA']

        if self.use_cache:
            self._save_cache()
        return True

    def logout(self):
        url_login = f"{self.base_url}api/logout"
        r = self.s.get(
            url_login,
            verify=self.verify_tls
        )
        if r.status_code == 200:
            self._sessionid = None
            if self.use_cache:
                self._delete_cache()

        return r.status_code

    def _prepare_url(self, command, params={}, config_path=None):
        params['UIDARUBA'] = self._sessionid
        params['json'] = 1
        if config_path is not None:
            params['config_path'] = config_path
        return f"{self.base_url}configuration/{command}?{urlencode(params)}"

    def _make_request(self, method_ptr, args={}):
        args['verify'] = self.verify_tls
        r = method_ptr(**args)
        if r.status_code == 200:
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                if r.text == '':
                    return dict()
        else:
            r.raise_for_status()

    def get(self, command, params={}, config_path=None):
        return self._make_request(self.s.get, {
            'url': self._prepare_url(command, params, config_path)
        })

    def post(self, command, payload=None, params={}, config_path=None):
        return self._make_request(self.s.post, {
            'url': self._prepare_url(command, params, config_path),
            'json': payload
        })

    def put(self, command, payload, params={}, config_path=None):
        return self._make_request(self.s.put,{
            'url': self._prepare_url(command, params, config_path),
            'json': payload
        })

    def write(self):
        self.post("write_memory")

    def show(self, command):
        return self.get("showcommand", params={'command': command})

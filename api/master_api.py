import requests
from typing import Dict, List
from config import API_TIMEOUT


class MasterAPI:
    def __init__(self, base_url: str, token: str | None = None):
        base_url = base_url.strip().rstrip("/")
        if not base_url.endswith("/api"):
            base_url = f"{base_url}/api"
        self.base_url = base_url
        self.token = token

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def init(self, uid: str) -> Dict:
        url = self._url("/terminal/init")
        r = requests.post(url, json={"uid": uid}, headers=self._headers(), timeout=API_TIMEOUT)
        data = r.json() if r.content else {}
        data = data if isinstance(data, dict) else {}
        if r.status_code == 200 and data.get("success"):
            return {"token": data.get("token", ""), "info": data.get("info", {}), "pairs": data.get("pairs", [])}
        if r.status_code in (401, 403):
            raise PermissionError(data.get("message", "Auth error"))
        raise RuntimeError(data.get("message", f"Init error {r.status_code}"))

    def get_status(self) -> Dict:
        url = self._url("/data/status")
        r = requests.get(url, headers=self._headers(), timeout=API_TIMEOUT)
        data = r.json() if r.content else {}
        data = data if isinstance(data, dict) else {}
        if r.status_code == 200 and data.get("success"):
            return data
        if r.status_code == 401:
            raise PermissionError("Token invalid or expired")
        raise RuntimeError(data.get("message", f"Status error {r.status_code}"))

    def get_orders(self) -> Dict:
        url = self._url("/data/orders")
        r = requests.get(url, headers=self._headers(), timeout=API_TIMEOUT)
        data = r.json() if r.content else {}
        data = data if isinstance(data, dict) else {}
        if r.status_code == 200 and data.get("success"):
            return data
        if r.status_code == 401:
            raise PermissionError("Token invalid or expired")
        raise RuntimeError(data.get("message", f"Orders error {r.status_code}"))

    def send_log(self, data: Dict) -> Dict:
        url = self._url("/data/log")
        r = requests.post(url, json=data, headers=self._headers(), timeout=API_TIMEOUT)
        resp = r.json() if r.content else {}
        resp = resp if isinstance(resp, dict) else {}
        if r.status_code == 200:
            return resp
        return {"success": False, "message": resp.get("message", "Log send error")}

    def open_trade(self, data: Dict) -> Dict:
        url = self._url("/data/trade/open")
        r = requests.post(url, json=data, headers=self._headers(), timeout=API_TIMEOUT)
        resp = r.json() if r.content else {}
        resp = resp if isinstance(resp, dict) else {}
        if r.status_code == 200 and resp.get("success"):
            return resp
        raise RuntimeError(resp.get("message", "Open trade error"))

    def close_trade(self, data: Dict) -> Dict:
        url = self._url("/data/trade/close")
        r = requests.post(url, json=data, headers=self._headers(), timeout=API_TIMEOUT)
        resp = r.json() if r.content else {}
        resp = resp if isinstance(resp, dict) else {}
        if r.status_code == 200 and resp.get("success"):
            return resp
        raise RuntimeError(resp.get("message", "Close trade error"))

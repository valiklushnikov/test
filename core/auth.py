from typing import Optional, Tuple, Dict, List
from api.master_api import MasterAPI
from utils.validators import is_valid_uuid, is_valid_url


class AuthManager:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger
        self._token: Optional[str] = None
        self._info: Dict = {}
        self._pairs: Dict = {}

    def login(self, url: str, uid: str) -> Tuple[str, Dict, Dict]:
        if not is_valid_url(url):
            raise ValueError("Invalid URL")
        if not is_valid_uuid(uid):
            raise ValueError("Invalid UID")
        api = MasterAPI(url)
        res = api.init(uid)
        self._token = res.get("token", "")
        info = res.get("info", {})
        self._info = info if isinstance(info, dict) else {}
        self._info["uid"] = uid
        self._pairs = res.get("pairs", {})
        self.settings.set("api_url", url)
        self.settings.set("token", self._token)
        self.settings.set("uid", uid)  # Сохраняем UID для авто-логина
        # Pairs теперь сохраняются в БД через App, здесь только кэш
        self.settings.save()
        return self._token, self._info, self._pairs

    def refresh_token(self) -> str:
        url = self.settings.get("api_url", "")
        if not url:
            return self._token or ""
        api = MasterAPI(url, self._token)
        # uid может отсутствовать в self._info после перезапуска, берем из settings или кэша
        uid = self._info.get("uid") or self.settings.get("uid", "")
        if not uid:
             # Если uid потерян, пробуем просто init без uid (если API позволяет) или не обновляем
             # В данном случае, лучше вернуть текущий токен
             return self._token or ""
             
        res = api.init(uid)
        self._token = res.get("token", self._token)
        self._pairs = res.get("pairs", self._pairs)
        return self._token

    def logout(self):
        self._token = None
        self._info = {}
        self._pairs = {}

    def is_authenticated(self) -> bool:
        return bool(self._token)

    def get_token(self) -> str:
        return self._token or ""

    def save_session(self):
        pass

    def load_session(self):
        try:
            token = self.settings.get("token", "")
            uid = self.settings.get("uid", "")
            # Пары грузятся из БД в App
            if token:
                self._token = token
            if uid:
                self._info["uid"] = uid
        except Exception:
            self._token = None
            self._pairs = {}

    def get_pairs(self) -> Dict:
        return dict(self._pairs)

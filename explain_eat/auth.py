import hashlib
import json
from pathlib import Path
from typing import Any, Dict

USER_STORE = Path(__file__).resolve().parent.parent / "users.json"


def _ensure_store() -> None:
    if not USER_STORE.exists():
        USER_STORE.write_text("{}", encoding="utf-8")


def _load_users() -> Dict[str, Any]:
    _ensure_store()
    try:
        data = USER_STORE.read_text(encoding="utf-8")
        return json.loads(data)
    except (json.JSONDecodeError, OSError):
        USER_STORE.write_text("{}", encoding="utf-8")
        return {}


def _write_users(users: Dict[str, Any]) -> None:
    USER_STORE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(username: str, password: str, profile: Dict[str, Any] | None = None) -> bool:
    username = username.strip()
    if not username or not password:
        raise ValueError("Username and password must not be empty.")
    users = _load_users()
    if username in users:
        return False
    users[username] = {
        "password": _hash_password(password),
        "profile": profile or {},
    }
    _write_users(users)
    return True


def login_user(username: str, password: str) -> Dict[str, Any] | None:
    users = _load_users()
    user_data = users.get(username.strip())
    if not isinstance(user_data, dict):
        return None
    if user_data.get("password") == _hash_password(password):
        return user_data.get("profile", {})
    return None

from contextvars import ContextVar
from pathlib import Path
import hashlib
import re
import shutil


DEFAULT_LOCAL_USER_ID = "local-dev"

TOKEN_DIRECTORY = Path(
    "user_tokens"
)


_current_user_id = ContextVar(
    "inbox_assistant_current_user_id",
    default=DEFAULT_LOCAL_USER_ID,
)


def normalize_user_id(
    user_id,
):
    value = str(
        user_id
        or DEFAULT_LOCAL_USER_ID
    ).strip()

    if not value:
        value = DEFAULT_LOCAL_USER_ID

    return value


def make_google_user_id(
    google_subject,
):
    subject = str(
        google_subject
        or ""
    ).strip()

    if not subject:
        raise ValueError(
            "Google účet nemá platný "
            "identifikátor uživatele."
        )

    return f"google:{subject}"


def set_current_user_id(
    user_id,
):
    normalized = normalize_user_id(
        user_id
    )

    _current_user_id.set(
        normalized
    )

    return normalized


def get_current_user_id():
    return normalize_user_id(
        _current_user_id.get()
    )


def make_safe_user_token_name(
    user_id=None,
):
    normalized = normalize_user_id(
        user_id
        or get_current_user_id()
    )

    readable = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "_",
        normalized,
    ).strip(
        "._-"
    )

    if not readable:
        readable = "user"

    digest = hashlib.sha256(
        normalized.encode(
            "utf-8"
        )
    ).hexdigest()[:12]

    return (
        f"{readable[:40]}_{digest}"
    )


def get_user_token_path(
    user_id=None,
):
    TOKEN_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    token_name = (
        make_safe_user_token_name(
            user_id
        )
    )

    return (
        TOKEN_DIRECTORY
        / f"{token_name}.json"
    )


def migrate_legacy_token_if_needed(
    user_id=None,
):
    """
    Starý token.json smí být převzat pouze
    původním lokálním profilem local-dev.

    Novému Google uživateli nikdy nesmíme
    zkopírovat token jiného účtu.
    """

    normalized_user_id = normalize_user_id(
        user_id
        or get_current_user_id()
    )

    target = get_user_token_path(
        normalized_user_id
    )

    if target.exists():
        return target

    if (
        normalized_user_id
        != DEFAULT_LOCAL_USER_ID
    ):
        return target

    legacy = Path(
        "token.json"
    )

    if legacy.exists():
        shutil.copy2(
            legacy,
            target,
        )

    return target
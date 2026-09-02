import streamlit as st

from datetime import datetime
from email.utils import parsedate_to_datetime

from backend import (
    analyze_inbox,
    trash_message,
    mark_resolved,
    mark_unresolved,
    mark_read,
    mark_unread,
    mark_to_do,
    remove_to_do,
    perform_one_click_unsubscribe,
    get_app_settings,
    save_app_settings,
    should_skip_trash_confirmation,
    record_trash_action,
    record_unsubscribe_action,
    clear_unsubscribe_history_for,
    get_search_index_stats,
    index_gmail_period,
    search_email_index,
    remove_from_search_index,
    save_search_feedback,
    save_search_alias,
    delete_search_alias,
    get_search_aliases,
    save_sender_classification_rule,
    delete_sender_classification_rule,
    get_sender_classification_rules,
    claim_local_dev_database_data,
)

from user_context import (
    get_current_user_id,
    make_google_user_id,
    set_current_user_id,
)


APP_VERSION = "0.13.0"


st.set_page_config(
    page_title="Inbox Assistant",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if not st.user.is_logged_in:
    st.title(
        "📬 Inbox Assistant"
    )

    st.write(
        "Pro pokračování se přihlas "
        "svým Google účtem."
    )

    if st.button(
        "🔐 Přihlásit přes Google",
        type="primary",
    ):
        st.login()

    st.stop()

google_subject = st.user.get(
    "sub"
)

user_id = make_google_user_id(
    google_subject
)

set_current_user_id(
    user_id
)

claim_local_dev_database_data(
    user_id
)


# ==================================================
# CSS
# ==================================================

st.markdown(
    """
    <style>

    section[data-testid="stSidebar"][aria-expanded="true"] {
        width: 350px !important;
        min-width: 350px !important;
    }

    section[data-testid="stSidebar"][aria-expanded="true"] > div {
        width: 350px !important;
    }

    section[data-testid="stSidebar"] .stMarkdown {
        font-size: 12px;
        line-height: 1.35;
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 24px;
    }

    section[data-testid="stSidebar"] h2 {
        font-size: 18px;
    }

    section[data-testid="stSidebar"] li {
        font-size: 12px;
        line-height: 1.35;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 10px;
    }

    div.stButton > button,
    div.stLinkButton > a {
        white-space: nowrap;
    }

    .status-badges {
        margin-top: 4px;
        margin-bottom: 12px;
    }

    .status-badge {
        display: inline-block;
        padding: 3px 9px;
        margin-right: 6px;
        margin-bottom: 4px;
        border-radius: 999px;
        background-color:
            rgba(120, 120, 120, 0.16);
        font-size: 12px;
        font-weight: 600;
    }

    .search-score {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        background-color:
            rgba(120, 120, 120, 0.16);
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# HELPERS
# ==================================================

def read_markdown_file(
    path
):
    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return file.read()

    except FileNotFoundError:
        return (
            f"Soubor {path} nebyl nalezen."
        )


def parse_changelog(
    path="CHANGELOG.md"
):
    content = read_markdown_file(
        path
    )

    sections = []
    current_version = None
    current_lines = []

    for line in content.splitlines():
        if line.startswith(
            "## "
        ):
            if current_version is not None:
                sections.append(
                    {
                        "version":
                            current_version,

                        "content":
                            "\n".join(
                                current_lines
                            ).strip(),
                    }
                )

            current_version = (
                line[3:].strip()
            )

            current_lines = []

        elif current_version is not None:
            current_lines.append(
                line
            )

    if current_version is not None:
        sections.append(
            {
                "version":
                    current_version,

                "content":
                    "\n".join(
                        current_lines
                    ).strip(),
            }
        )

    return sections


def remove_email_from_session(
    message_id
):
    st.session_state[
        "emails"
    ] = [
        email
        for email
        in st.session_state[
            "emails"
        ]
        if (
            email[
                "message_id"
            ]
            != message_id
        )
    ]


def select_index(
    options,
    current_value,
    fallback_index,
):
    if current_value in options:
        return options.index(
            current_value
        )

    return fallback_index


def request_search():
    st.session_state[
        "search_requested"
    ] = True


def format_received_at(
    raw_date
):
    if (
        not raw_date
        or raw_date == "(neuvedeno)"
    ):
        return (
            "datum přijetí neznámé"
        )

    try:
        received = parsedate_to_datetime(
            raw_date
        )

        if received.tzinfo is not None:
            received = (
                received.astimezone()
            )

        now = datetime.now(
            received.tzinfo
        )

        received_date = (
            received.date()
        )

        today = now.date()

        difference = (
            today
            - received_date
        ).days

        time_text = (
            received.strftime(
                "%H:%M"
            )
        )

        if difference == 0:
            return (
                f"dnes v {time_text}"
            )

        if difference == 1:
            return (
                f"včera v {time_text}"
            )

        formatted_date = (
            f"{received.day}. "
            f"{received.month}. "
            f"{received.year} "
            f"v {time_text}"
        )

        if difference < 7:
            relative = (
                f"před {difference} dny"
            )

        elif difference < 14:
            relative = (
                "před týdnem"
            )

        elif difference < 30:
            weeks = max(
                2,
                round(
                    difference / 7
                ),
            )

            relative = (
                f"před {weeks} týdny"
            )

        else:
            months = (
                (
                    today.year
                    - received_date.year
                )
                * 12
                + (
                    today.month
                    - received_date.month
                )
            )

            if months <= 1:
                relative = (
                    "před měsícem"
                )

            elif months < 12:
                relative = (
                    f"před {months} měsíci"
                )

            else:
                years = max(
                    1,
                    round(
                        difference / 365
                    ),
                )

                if years == 1:
                    relative = (
                        "před rokem"
                    )

                else:
                    relative = (
                        f"před {years} lety"
                    )

        return (
            f"{formatted_date} · {relative}"
        )

    except Exception:
        return raw_date


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.title(
        "📬 Inbox Assistant"
    )

    if st.user.is_logged_in:
        current_email = st.user.get(
            "email",
            ""
        )

        st.markdown(
            """
            <div style="
                margin-top: 8px;
                margin-bottom: 6px;
                font-size: 12px;
                font-weight: 600;
                opacity: 0.65;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            ">
                AKTUÁLNÍ SCHRÁNKA
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="
                padding: 10px 12px;
                margin-bottom: 10px;
                border-radius: 8px;
                background: rgba(120, 120, 120, 0.14);
                font-size: 15px;
                font-weight: 700;
                word-break: break-word;
            ">
                {current_email}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Odhlásit",
            type="primary",
            use_container_width=True,
        ):
            st.logout()

    st.divider()

    st.markdown(
        "### Changelog"
    )

    changelog_sections = (
        parse_changelog()
    )

    if changelog_sections:
        for index, section in enumerate(
            changelog_sections
        ):
            with st.expander(
                section[
                    "version"
                ],
                expanded=(
                    index == 0
                ),
            ):
                st.markdown(
                    section[
                        "content"
                    ]
                )
    else:
        st.caption(
            "Changelog je zatím prázdný."
        )

    st.divider()

    st.caption(
        f"Verze {APP_VERSION}"
    )

    st.caption(
        (
            "Interní profil: "
            f"{get_current_user_id()}"
        )
    )


# ==================================================
# HLAVIČKA + NASTAVENÍ
# ==================================================

header_col1, header_col2 = (
    st.columns(
        [8, 1]
    )
)

with header_col1:
    st.title(
        "📬 Inbox Assistant"
    )

    st.caption(
        "AI přehled a chytré vyhledávání "
        "v e-mailové schránce."
    )


with header_col2:
    with st.popover(
        "⚙️ Nastavení",
        use_container_width=True,
    ):
        current_settings = (
            get_app_settings()
        )

        st.subheader(
            "Automatizace koše"
        )

        smart_trash_enabled = (
            st.toggle(
                "Přeskakovat potvrzení",
                value=current_settings[
                    "smart_trash_enabled"
                ],
            )
        )

        trash_threshold_options = [
            2,
            3,
            4,
            5,
            10,
        ]

        smart_trash_threshold = (
            st.selectbox(
                "Počet předchozích smazání",
                options=trash_threshold_options,
                index=select_index(
                    trash_threshold_options,
                    current_settings[
                        "smart_trash_threshold"
                    ],
                    1,
                ),
                disabled=(
                    not smart_trash_enabled
                ),
            )
        )

        days_options = [
            7,
            14,
            30,
            60,
            90,
        ]

        smart_trash_days = (
            st.selectbox(
                "Časové okno koše",
                options=days_options,
                format_func=lambda days:
                    f"{days} dní",
                index=select_index(
                    days_options,
                    current_settings[
                        "smart_trash_days"
                    ],
                    2,
                ),
                disabled=(
                    not smart_trash_enabled
                ),
            )
        )

        st.divider()

        st.subheader(
            "Newslettery"
        )

        remember_unsubscribe = (
            st.toggle(
                "Pamatovat si odhlášení",
                value=current_settings[
                    "remember_unsubscribe"
                ],
            )
        )

        unsubscribe_history_days = (
            st.selectbox(
                "Platnost historie odhlášení",
                options=days_options,
                format_func=lambda days:
                    f"{days} dní",
                index=select_index(
                    days_options,
                    current_settings[
                        "unsubscribe_history_days"
                    ],
                    2,
                ),
                disabled=(
                    not remember_unsubscribe
                ),
            )
        )

        if st.button(
            "💾 Uložit nastavení",
            type="primary",
            use_container_width=True,
        ):
            save_app_settings(
                smart_trash_enabled,
                smart_trash_threshold,
                smart_trash_days,
                remember_unsubscribe,
                unsubscribe_history_days,
            )

            st.toast(
                "Nastavení bylo uloženo.",
                icon="✅",
            )


# ==================================================
# SESSION STATE
# ==================================================

if "emails" not in st.session_state:
    st.session_state[
        "emails"
    ] = []

if "confirm_trash" not in st.session_state:
    st.session_state[
        "confirm_trash"
    ] = None

if "confirm_unsubscribe" not in st.session_state:
    st.session_state[
        "confirm_unsubscribe"
    ] = None

if "unsubscribe_fallbacks" not in st.session_state:
    st.session_state[
        "unsubscribe_fallbacks"
    ] = {}

if "search_results" not in st.session_state:
    st.session_state[
        "search_results"
    ] = []

if "search_query_used" not in st.session_state:
    st.session_state[
        "search_query_used"
    ] = ""

if "search_candidate_offset" not in st.session_state:
    st.session_state[
        "search_candidate_offset"
    ] = 0

if "search_alias_matches" not in st.session_state:
    st.session_state[
        "search_alias_matches"
    ] = []

if "search_time_filter" not in st.session_state:
    st.session_state[
        "search_time_filter"
    ] = None

if "confirm_full_index" not in st.session_state:
    st.session_state[
        "confirm_full_index"
    ] = False

if "search_requested" not in st.session_state:
    st.session_state[
        "search_requested"
    ] = False


# ==================================================
# KOŠ
# ==================================================

def perform_trash(
    email,
    smart_skip=False,
    previous_count=0,
):
    message_id = email[
        "message_id"
    ]

    sender_email = email.get(
        "sender_email"
    )

    trash_message(
        message_id
    )

    record_trash_action(
        sender_email,
        message_id,
    )

    remove_from_search_index(
        message_id
    )

    remove_email_from_session(
        message_id
    )

    st.session_state[
        "confirm_trash"
    ] = None

    if smart_skip:
        st.toast(
            (
                "E-mail přesunut do koše. "
                f"Potvrzení přeskočeno – "
                f"{previous_count} předchozích "
                f"smazání od stejného odesílatele."
            ),
            icon="🗑️",
        )

    else:
        st.toast(
            "E-mail byl přesunut do koše.",
            icon="🗑️",
        )

    st.rerun()


def render_trash_controls(
    email
):
    message_id = email[
        "message_id"
    ]

    sender_email = email.get(
        "sender_email"
    )

    if (
        st.session_state[
            "confirm_trash"
        ]
        == message_id
    ):
        st.warning(
            "Opravdu přesunout tento e-mail do koše?"
        )

        confirm_col, cancel_col = (
            st.columns(
                2
            )
        )

        with confirm_col:
            if st.button(
                "✅ Ano",
                key=f"confirm_{message_id}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    perform_trash(
                        email
                    )

                except Exception as error:
                    st.error(
                        f"Přesun do koše selhal: {error}"
                    )

        with cancel_col:
            if st.button(
                "Zrušit",
                key=f"cancel_{message_id}",
                use_container_width=True,
            ):
                st.session_state[
                    "confirm_trash"
                ] = None

                st.rerun()

    else:
        if st.button(
            "🗑 Koš",
            key=f"trash_{message_id}",
            use_container_width=True,
        ):
            try:
                (
                    should_skip,
                    previous_count,
                ) = (
                    should_skip_trash_confirmation(
                        sender_email
                    )
                )

                if should_skip:
                    perform_trash(
                        email,
                        smart_skip=True,
                        previous_count=previous_count,
                    )

                else:
                    st.session_state[
                        "confirm_trash"
                    ] = message_id

                    st.rerun()

            except Exception as error:
                st.error(
                    f"Kontrola historie koše selhala: {error}"
                )


# ==================================================
# PŘEČTENO
# ==================================================

def render_read_control(
    email
):
    message_id = email[
        "message_id"
    ]

    if email[
        "is_unread"
    ]:
        if st.button(
            "👁 Přečíst",
            key=f"read_{message_id}",
            use_container_width=True,
        ):
            mark_read(
                message_id
            )

            email[
                "is_unread"
            ] = False

            st.rerun()

    else:
        if st.button(
            "📩 Nepřečíst",
            key=f"unread_{message_id}",
            use_container_width=True,
        ):
            mark_unread(
                message_id
            )

            email[
                "is_unread"
            ] = True

            st.rerun()


# ==================================================
# K ŘEŠENÍ
# ==================================================

def render_todo_control(
    email
):
    message_id = email[
        "message_id"
    ]

    if email[
        "is_to_do"
    ]:
        if st.button(
            "📌 Odebrat",
            key=f"remove_todo_{message_id}",
            use_container_width=True,
        ):
            remove_to_do(
                message_id
            )

            email[
                "is_to_do"
            ] = False

            st.rerun()

    else:
        if st.button(
            "📌 K řešení",
            key=f"todo_{message_id}",
            use_container_width=True,
        ):
            mark_to_do(
                message_id
            )

            remove_email_from_session(
                message_id
            )

            st.toast(
                "E-mail označen jako K řešení.",
                icon="📌",
            )

            st.rerun()


# ==================================================
# VYŘEŠENO
# ==================================================

def render_resolved_control(
    email
):
    message_id = email[
        "message_id"
    ]

    if email[
        "is_resolved"
    ]:
        if st.button(
            "↩ Nevyřešeno",
            key=f"unresolve_{message_id}",
            use_container_width=True,
        ):
            mark_unresolved(
                message_id
            )

            remove_email_from_session(
                message_id
            )

            st.rerun()

    else:
        if st.button(
            "✅ Vyřešeno",
            key=f"resolve_{message_id}",
            use_container_width=True,
        ):
            mark_resolved(
                message_id
            )

            remove_email_from_session(
                message_id
            )

            st.toast(
                "E-mail označen jako vyřešený.",
                icon="✅",
            )

            st.rerun()


# ==================================================
# ODHLAŠOVÁNÍ
# ==================================================

def render_unsubscribe_control(
    email
):
    message_id = email[
        "message_id"
    ]

    sender_email = email.get(
        "sender_email"
    )

    unsubscribe_url = email.get(
        "unsubscribe_url"
    )

    fallback_url = (
        email.get(
            "unsubscribe_fallback_url"
        )
        or unsubscribe_url
    )

    method = email.get(
        "unsubscribe_method"
    )

    recent = email.get(
        "recent_unsubscribe"
    )

    active_fallback = (
        st.session_state[
            "unsubscribe_fallbacks"
        ].get(
            message_id
        )
    )

    if recent:
        if (
            recent[
                "action_type"
            ]
            == "one_click_sent"
        ):
            label = (
                "✅ Odhlášení požadováno"
            )

        else:
            label = (
                "🕓 Odhlášení řešeno"
            )

        st.button(
            label,
            key=f"recent_unsub_{message_id}",
            disabled=True,
            use_container_width=True,
        )

        if st.button(
            "↩ Nabídnout znovu",
            key=f"reset_unsub_{message_id}",
            use_container_width=True,
        ):
            clear_unsubscribe_history_for(
                sender_email,
                unsubscribe_url,
            )

            email[
                "recent_unsubscribe"
            ] = None

            st.rerun()

        return

    if active_fallback:
        st.warning(
            (
                "Automatické odhlášení server odmítl "
                f"({active_fallback['error']}). "
                "Můžeš ho dokončit ručně."
            )
        )

        st.link_button(
            "🌐 Otevřít odhlašovací stránku",
            active_fallback[
                "url"
            ],
            use_container_width=True,
        )

        if st.button(
            "✅ Odhlášení provedeno",
            key=f"fallback_done_{message_id}",
            use_container_width=True,
        ):
            record_unsubscribe_action(
                sender_email,
                unsubscribe_url,
                "link_completed",
            )

            email[
                "recent_unsubscribe"
            ] = {
                "action_type":
                    "link_completed",
                "action_at":
                    "",
            }

            st.session_state[
                "unsubscribe_fallbacks"
            ].pop(
                message_id,
                None,
            )

            st.toast(
                "Odhlášení bylo uloženo do historie.",
                icon="✅",
            )

            st.rerun()

        return

    if not email[
        "unsubscribe_available"
    ]:
        return

    if method == "one_click_post":
        if (
            st.session_state[
                "confirm_unsubscribe"
            ]
            == message_id
        ):
            st.warning(
                "Opravdu se chceš odhlásit "
                "z tohoto newsletteru?"
            )

            confirm_col, cancel_col = (
                st.columns(
                    2
                )
            )

            with confirm_col:
                if st.button(
                    "✅ Odhlásit",
                    key=f"confirm_unsubscribe_{message_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    result = (
                        perform_one_click_unsubscribe(
                            unsubscribe_url
                        )
                    )

                    if result[
                        "success"
                    ]:
                        record_unsubscribe_action(
                            sender_email,
                            unsubscribe_url,
                            "one_click_sent",
                        )

                        email[
                            "recent_unsubscribe"
                        ] = {
                            "action_type":
                                "one_click_sent",
                            "action_at":
                                "",
                        }

                        st.session_state[
                            "confirm_unsubscribe"
                        ] = None

                        st.toast(
                            "Požadavek na odhlášení byl odeslán.",
                            icon="✅",
                        )

                        st.rerun()

                    else:
                        st.session_state[
                            "confirm_unsubscribe"
                        ] = None

                        if (
                            result.get(
                                "fallback_allowed"
                            )
                            and fallback_url
                        ):
                            st.session_state[
                                "unsubscribe_fallbacks"
                            ][
                                message_id
                            ] = {
                                "url":
                                    fallback_url,

                                "error":
                                    result.get(
                                        "error",
                                        "chyba serveru",
                                    ),
                            }

                            st.rerun()

                        else:
                            st.error(
                                (
                                    "Odhlášení se nepodařilo. "
                                    f"{result.get('error')}"
                                )
                            )

            with cancel_col:
                if st.button(
                    "Zrušit",
                    key=f"cancel_unsubscribe_{message_id}",
                    use_container_width=True,
                ):
                    st.session_state[
                        "confirm_unsubscribe"
                    ] = None

                    st.rerun()

        else:
            if st.button(
                "🚫 Odhlásit",
                key=f"unsubscribe_post_{message_id}",
                use_container_width=True,
            ):
                st.session_state[
                    "confirm_unsubscribe"
                ] = message_id

                st.rerun()

    else:
        st.link_button(
            "🚫 Odhlásit",
            unsubscribe_url,
            use_container_width=True,
        )

        if st.button(
            "✅ Odhlášení provedeno",
            key=f"mark_unsub_{message_id}",
            use_container_width=True,
        ):
            record_unsubscribe_action(
                sender_email,
                unsubscribe_url,
                "link_completed",
            )

            email[
                "recent_unsubscribe"
            ] = {
                "action_type":
                    "link_completed",
                "action_at":
                    "",
            }

            st.toast(
                "Odhlášení bylo uloženo do historie.",
                icon="✅",
            )

            st.rerun()


# ==================================================
# KLASIFIKAČNÍ FEEDBACK
# ==================================================

def render_classification_control(
    email,
    currently_newsletter,
):
    message_id = email[
        "message_id"
    ]

    sender_email = email.get(
        "sender_email"
    )

    if not sender_email:
        return

    current_rule = email.get(
        "classification_rule"
    )

    if currently_newsletter:
        if (
            current_rule
            == "always_newsletter"
        ):
            st.caption(
                "🧠 Tento odesílatel je uložen jako "
                "„Vždy newsletter/reklama“."
            )

        if st.button(
            "🚫 Není newsletter/reklama",
            key=f"not_newsletter_{message_id}",
        ):
            save_sender_classification_rule(
                sender_email,
                "not_newsletter",
            )

            email[
                "classification_rule"
            ] = "not_newsletter"

            email[
                "analysis"
            ].category = "na vědomí"

            st.toast(
                (
                    "Zapamatováno. E-maily od tohoto "
                    "odesílatele už nebudou automaticky "
                    "řazeny mezi newslettery/reklamu."
                ),
                icon="🧠",
            )

            st.rerun()

    else:
        if (
            current_rule
            == "not_newsletter"
        ):
            st.caption(
                "🧠 Tento odesílatel je uložen jako "
                "„Není newsletter/reklama“."
            )

        if st.button(
            "📰 Vždy newsletter/reklama",
            key=f"always_newsletter_{message_id}",
        ):
            save_sender_classification_rule(
                sender_email,
                "always_newsletter",
            )

            email[
                "classification_rule"
            ] = "always_newsletter"

            email[
                "analysis"
            ].category = "newsletter"

            email[
                "analysis"
            ].needs_action = False

            email[
                "analysis"
            ].action = "Žádná akce"

            st.toast(
                (
                    "Zapamatováno. E-maily od tohoto "
                    "odesílatele budou řazeny mezi "
                    "newslettery/reklamu."
                ),
                icon="🧠",
            )

            st.rerun()


# ==================================================
# STATUS
# ==================================================

def render_email_status(
    email
):
    badges = []

    if email[
        "is_unread"
    ]:
        badges.append(
            "📩 Nepřečtené"
        )

    else:
        badges.append(
            "👁 Přečtené"
        )

    if email[
        "is_to_do"
    ]:
        badges.append(
            "📌 K řešení"
        )

    if email[
        "is_resolved"
    ]:
        badges.append(
            "✅ Vyřešeno"
        )

    badge_html = "".join(
        (
            '<span class="status-badge">'
            f"{badge}"
            "</span>"
        )
        for badge in badges
    )

    st.markdown(
        (
            '<div class="status-badges">'
            f"{badge_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


# ==================================================
# AKČNÍ ŘÁDEK
# ==================================================

def render_common_actions(
    email,
    include_unsubscribe=False,
):
    show_unsubscribe = (
        include_unsubscribe
        and (
            email[
                "unsubscribe_available"
            ]
            or email.get(
                "recent_unsubscribe"
            )
            or (
                email[
                    "message_id"
                ]
                in st.session_state[
                    "unsubscribe_fallbacks"
                ]
            )
        )
    )

    if show_unsubscribe:
        columns = st.columns(
            6,
            gap="small",
        )

        with columns[0]:
            st.link_button(
                "📨 Gmail",
                email[
                    "gmail_link"
                ],
                use_container_width=True,
            )

        with columns[1]:
            render_unsubscribe_control(
                email
            )

        with columns[2]:
            render_read_control(
                email
            )

        with columns[3]:
            render_todo_control(
                email
            )

        with columns[4]:
            render_resolved_control(
                email
            )

        with columns[5]:
            render_trash_controls(
                email
            )

    else:
        columns = st.columns(
            5,
            gap="small",
        )

        with columns[0]:
            st.link_button(
                "📨 Gmail",
                email[
                    "gmail_link"
                ],
                use_container_width=True,
            )

        with columns[1]:
            render_read_control(
                email
            )

        with columns[2]:
            render_todo_control(
                email
            )

        with columns[3]:
            render_resolved_control(
                email
            )

        with columns[4]:
            render_trash_controls(
                email
            )


# ==================================================
# ZÁLOŽKY
# ==================================================

inbox_tab, search_tab = st.tabs(
    [
        "📬 Inbox",
        "🔎 AI vyhledávání",
    ]
)


# ==================================================
# INBOX
# ==================================================

with inbox_tab:
    st.subheader(
        "Nastavení analýzy"
    )

    settings_col1, settings_col2 = (
        st.columns(
            [2, 1]
        )
    )

    with settings_col1:
        email_count = st.selectbox(
            "Počet e-mailů",
            options=[
                5,
                10,
                20,
                50,
            ],
            index=0,
            key="email_count",
        )

    with settings_col2:
        show_tagged = st.checkbox(
            "Zobrazit i označené",
            value=False,
            key="show_tagged",
        )

    if st.button(
        "🔍 Zkontrolovat inbox",
        type="primary",
        key="analyze_inbox_button",
    ):
        try:
            with st.spinner(
                "Analyzuji e-maily..."
            ):
                emails = analyze_inbox(
                    max_emails=email_count,
                    show_tagged=show_tagged,
                )

            st.session_state[
                "emails"
            ] = emails

            st.session_state[
                "confirm_trash"
            ] = None

            st.session_state[
                "confirm_unsubscribe"
            ] = None

        except Exception as error:
            st.error(
                f"Analýza inboxu selhala: {error}"
            )

    emails = st.session_state[
        "emails"
    ]

    if emails:
        st.divider()

        st.caption(
            f"Zobrazeno {len(emails)} "
            "analyzovaných e-mailů."
        )

        action_emails = [
            email
            for email in emails
            if email[
                "analysis"
            ].needs_action
        ]

        info_emails = [
            email
            for email in emails
            if (
                not email[
                    "analysis"
                ].needs_action
                and email[
                    "analysis"
                ].category
                not in [
                    "newsletter",
                    "reklama",
                ]
            )
        ]

        newsletter_emails = [
            email
            for email in emails
            if email[
                "analysis"
            ].category
            in [
                "newsletter",
                "reklama",
            ]
        ]

        st.header(
            "🔴 Potřebuje tvoji pozornost"
        )

        if not action_emails:
            st.success(
                "Nic není potřeba řešit 🎉"
            )

        for email in action_emails:
            analysis = email[
                "analysis"
            ]

            with st.container(
                border=True
            ):
                st.subheader(
                    email[
                        "subject"
                    ]
                )

                st.caption(
                    f"Od: {email['sender']}"
                )

                st.caption(
                    (
                        "🕒 Přijato: "
                        f"{format_received_at(email.get('received_at'))}"
                    )
                )

                render_email_status(
                    email
                )

                st.write(
                    analysis.summary
                )

                st.markdown(
                    f"**Akce:** {analysis.action}"
                )

                st.markdown(
                    f"**Priorita:** {analysis.priority}"
                )

                st.markdown(
                    f"**Kategorie:** {analysis.category}"
                )

                if analysis.deadline:
                    st.markdown(
                        f"**Deadline:** {analysis.deadline}"
                    )

                if analysis.event_date:
                    st.markdown(
                        f"**Datum události:** {analysis.event_date}"
                    )

                if analysis.security_alert:
                    st.warning(
                        "🔐 Bezpečnostní upozornění"
                    )

                render_classification_control(
                    email,
                    currently_newsletter=False,
                )

                render_common_actions(
                    email
                )

        st.header(
            "🟡 Na vědomí"
        )

        if not info_emails:
            st.info(
                "Žádné informační e-maily."
            )

        for email in info_emails:
            analysis = email[
                "analysis"
            ]

            with st.container(
                border=True
            ):
                st.subheader(
                    email[
                        "subject"
                    ]
                )

                st.caption(
                    f"Od: {email['sender']}"
                )

                st.caption(
                    (
                        "🕒 Přijato: "
                        f"{format_received_at(email.get('received_at'))}"
                    )
                )

                render_email_status(
                    email
                )

                st.write(
                    analysis.summary
                )

                st.caption(
                    f"Kategorie: {analysis.category}"
                )

                if analysis.event_date:
                    st.markdown(
                        f"**Datum události:** {analysis.event_date}"
                    )

                render_classification_control(
                    email,
                    currently_newsletter=False,
                )

                render_common_actions(
                    email
                )

        st.header(
            "📰 Newslettery / reklama"
        )

        if not newsletter_emails:
            st.info(
                "Žádné newslettery."
            )

        for email in newsletter_emails:
            analysis = email[
                "analysis"
            ]

            with st.container(
                border=True
            ):
                st.subheader(
                    email[
                        "subject"
                    ]
                )

                st.caption(
                    f"Od: {email['sender']}"
                )

                st.caption(
                    (
                        "🕒 Přijato: "
                        f"{format_received_at(email.get('received_at'))}"
                    )
                )

                render_email_status(
                    email
                )

                st.write(
                    analysis.summary
                )

                if (
                    not email[
                        "unsubscribe_available"
                    ]
                    and not email.get(
                        "recent_unsubscribe"
                    )
                ):
                    st.caption(
                        "ℹ️ Odhlašovací odkaz "
                        "nebyl automaticky nalezen."
                    )

                render_classification_control(
                    email,
                    currently_newsletter=True,
                )

                render_common_actions(
                    email,
                    include_unsubscribe=True,
                )

    else:
        st.info(
            "Spusť analýzu inboxu."
        )

    st.divider()

    with st.expander(
        "🧠 Pravidla newsletterů podle odesílatele"
    ):
        rules = (
            get_sender_classification_rules()
        )

        if not rules:
            st.caption(
                "Zatím nejsou uložená žádná "
                "pravidla klasifikace."
            )

        else:
            for rule in rules:
                col1, col2 = st.columns(
                    [5, 1]
                )

                if (
                    rule[
                        "rule"
                    ]
                    == "not_newsletter"
                ):
                    label = (
                        "🚫 Není newsletter/reklama"
                    )

                else:
                    label = (
                        "📰 Vždy newsletter/reklama"
                    )

                with col1:
                    st.write(
                        (
                            f"**{rule['sender_email']}** "
                            f"→ {label}"
                        )
                    )

                with col2:
                    if st.button(
                        "🗑",
                        key=(
                            "delete_classification_"
                            f"{rule['sender_email']}"
                        ),
                        use_container_width=True,
                    ):
                        delete_sender_classification_rule(
                            rule[
                                "sender_email"
                            ]
                        )

                        st.rerun()


# ==================================================
# AI SEARCH
# ==================================================

with search_tab:
    st.subheader(
        "🔎 AI vyhledávání v e-mailech"
    )

    st.caption(
        "Vyhledávač kombinuje význam zpráv, "
        "AI hodnocení a tvoji předchozí zpětnou vazbu."
    )

    st.markdown(
        "#### 🧠 Co chceš najít?"
    )

    search_query = st.text_input(
        "Dotaz",
        placeholder=(
            "Např. faktury za poslední dva měsíce"
        ),
        key="semantic_search_query",
        on_change=request_search,
    )

    search_col1, search_col2, search_col3 = (
        st.columns(
            [1, 1, 1]
        )
    )

    with search_col1:
        result_count = st.selectbox(
            "Počet výsledků",
            options=[
                5,
                10,
                20,
                30,
            ],
            index=1,
            key="search_result_count",
        )

    with search_col2:
        sort_label = st.selectbox(
            "Řazení",
            options=[
                "Relevance",
                "Nejnovější",
            ],
            index=0,
            key="search_sort_mode",
        )

    with search_col3:
        st.write("")
        st.write("")

        if st.button(
            "🔎 Hledat",
            type="primary",
            use_container_width=True,
            key="search_button",
        ):
            st.session_state[
                "search_requested"
            ] = True

    sort_mode = (
        "newest"
        if (
            sort_label
            == "Nejnovější"
        )
        else "relevance"
    )

    if st.session_state[
        "search_requested"
    ]:
        st.session_state[
            "search_requested"
        ] = False

        if not search_query.strip():
            st.warning(
                "Nejdřív napiš, co chceš najít."
            )

        elif (
            get_search_index_stats()[
                "count"
            ]
            == 0
        ):
            st.warning(
                "Index je zatím prázdný. "
                "Nejdřív níže zaindexuj část schránky."
            )

        else:
            try:
                with st.spinner(
                    "Hledám kandidáty a AI "
                    "kontroluje jejich relevanci..."
                ):
                    result_package = (
                        search_email_index(
                            query=search_query,
                            limit=result_count,
                            sort_mode=sort_mode,
                            candidate_offset=0,
                            excluded_message_ids=set(),
                        )
                    )

                st.session_state[
                    "search_results"
                ] = (
                    result_package[
                        "results"
                    ]
                )

                st.session_state[
                    "search_query_used"
                ] = search_query

                st.session_state[
                    "search_candidate_offset"
                ] = (
                    result_package[
                        "next_offset"
                    ]
                )

                st.session_state[
                    "search_alias_matches"
                ] = (
                    result_package[
                        "aliases"
                    ]
                )

                st.session_state[
                    "search_time_filter"
                ] = (
                    result_package.get(
                        "time_filter"
                    )
                )

            except Exception as error:
                st.error(
                    f"Vyhledávání selhalo: {error}"
                )

    results = st.session_state[
        "search_results"
    ]

    query_used = st.session_state[
        "search_query_used"
    ]

    alias_matches = st.session_state[
        "search_alias_matches"
    ]

    time_filter = st.session_state[
        "search_time_filter"
    ]

    # ----------------------------------------------
    # DŮLEŽITÉ 0.12.0:
    # výsledky se přerovnají při každém rerunu UI,
    # takže změna selectboxu funguje okamžitě.
    # ----------------------------------------------

    display_results = list(
        results
    )

    if sort_mode == "newest":
        display_results.sort(
            key=lambda item:
                int(
                    item.get(
                        "internal_date",
                        0,
                    )
                    or 0
                ),
            reverse=True,
        )

    else:
        display_results.sort(
            key=lambda item:
                int(
                    item.get(
                        "relevance_score",
                        0,
                    )
                    or 0
                ),
            reverse=True,
        )

    if alias_matches:
        labels = []

        for alias in alias_matches:
            labels.append(
                (
                    f"{alias['alias']} → "
                    f"{alias['sender_name'] or alias['sender_email']}"
                )
            )

        st.info(
            "🧠 Použita naučená vazba: "
            + " · ".join(
                labels
            )
        )

    if time_filter:
        st.info(
            (
                "🕒 Použit časový filtr: "
                f"{time_filter['label']}"
            )
        )

    if display_results:
        st.divider()

        st.markdown(
            f"### Výsledky ({len(display_results)})"
        )

        if sort_mode == "newest":
            st.caption(
                "Relevantní výsledky jsou "
                "seřazené od nejnovějších."
            )

        else:
            st.caption(
                "Výsledky jsou seřazené podle "
                "AI hodnocení relevance."
            )

        for result in display_results:
            message_id = result[
                "message_id"
            ]

            with st.container(
                border=True
            ):
                st.subheader(
                    result[
                        "subject"
                    ]
                )

                st.caption(
                    f"Od: {result['sender']}"
                )

                if result[
                    "date_header"
                ]:
                    st.caption(
                        (
                            "🕒 Přijato: "
                            f"{format_received_at(result['date_header'])}"
                        )
                    )

                st.markdown(
                    (
                        '<span class="search-score">'
                        f'🧠 AI relevance: '
                        f'{result["relevance_score"]} %'
                        '</span>'
                    ),
                    unsafe_allow_html=True,
                )

                st.write(
                    result[
                        "summary"
                    ]
                )

                st.markdown(
                    (
                        "**Proč odpovídá dotazu:** "
                        f"{result['reason']}"
                    )
                )

                action_col1, action_col2, action_col3 = (
                    st.columns(
                        [2, 1, 1]
                    )
                )

                with action_col1:
                    st.link_button(
                        "📨 Otevřít v Gmailu",
                        result[
                            "gmail_link"
                        ],
                        use_container_width=True,
                    )

                with action_col2:
                    positive_label = (
                        "✅ Relevantní"
                        if (
                            result.get(
                                "feedback"
                            )
                            == 1
                        )
                        else "👍 Relevantní"
                    )

                    if st.button(
                        positive_label,
                        key=(
                            f"positive_feedback_"
                            f"{message_id}"
                        ),
                        use_container_width=True,
                    ):
                        save_search_feedback(
                            query=query_used,
                            message_id=message_id,
                            sender_email=result[
                                "sender_email"
                            ],
                            feedback=1,
                        )

                        result[
                            "feedback"
                        ] = 1

                        st.toast(
                            "Uloženo. Při příštím hledání "
                            "to asistent zohlední.",
                            icon="🧠",
                        )

                        st.rerun()

                with action_col3:
                    negative_label = (
                        "❌ Nerelevantní"
                        if (
                            result.get(
                                "feedback"
                            )
                            == -1
                        )
                        else "👎 Nerelevantní"
                    )

                    if st.button(
                        negative_label,
                        key=(
                            f"negative_feedback_"
                            f"{message_id}"
                        ),
                        use_container_width=True,
                    ):
                        save_search_feedback(
                            query=query_used,
                            message_id=message_id,
                            sender_email=result[
                                "sender_email"
                            ],
                            feedback=-1,
                        )

                        st.session_state[
                            "search_results"
                        ] = [
                            item
                            for item
                            in st.session_state[
                                "search_results"
                            ]
                            if (
                                item[
                                    "message_id"
                                ]
                                != message_id
                            )
                        ]

                        st.toast(
                            "Výsledek označen jako nerelevantní.",
                            icon="👎",
                        )

                        st.rerun()

                with st.expander(
                    "🧠 Naučit asistenta, kdo je tento odesílatel"
                ):
                    st.caption(
                        "Můžeš uložit například "
                        "„majitelka bytu“, „účetní“ "
                        "nebo „internetový provider“."
                    )

                    alias_value = st.text_input(
                        "Pojem",
                        placeholder=(
                            "např. majitelka bytu"
                        ),
                        key=(
                            f"alias_value_"
                            f"{message_id}"
                        ),
                    )

                    st.caption(
                        (
                            f"Bude spojeno s: "
                            f"{result['sender']}"
                        )
                    )

                    if st.button(
                        "💾 Zapamatovat",
                        key=(
                            f"save_alias_"
                            f"{message_id}"
                        ),
                    ):
                        if not alias_value.strip():
                            st.warning(
                                "Nejdřív napiš pojem."
                            )

                        else:
                            try:
                                save_search_alias(
                                    alias=alias_value,
                                    sender_name=result[
                                        "sender"
                                    ],
                                    sender_email=result[
                                        "sender_email"
                                    ],
                                )

                                st.toast(
                                    (
                                        f'Zapamatováno: '
                                        f'"{alias_value}"'
                                    ),
                                    icon="🧠",
                                )

                            except Exception as error:
                                st.error(
                                    f"Uložení se nepodařilo: {error}"
                                )

        st.write("")

        if st.button(
            "🔎 Najít další",
            use_container_width=True,
            key="find_more_button",
        ):
            try:
                existing_ids = {
                    item[
                        "message_id"
                    ]
                    for item
                    in st.session_state[
                        "search_results"
                    ]
                }

                with st.spinner(
                    "Kontroluji další kandidáty..."
                ):
                    more_package = (
                        search_email_index(
                            query=query_used,
                            limit=result_count,
                            sort_mode=sort_mode,
                            candidate_offset=(
                                st.session_state[
                                    "search_candidate_offset"
                                ]
                            ),
                            excluded_message_ids=existing_ids,
                        )
                    )

                new_results = (
                    more_package[
                        "results"
                    ]
                )

                if not new_results:
                    st.info(
                        "V další várce už AI "
                        "nenašla další použitelné výsledky."
                    )

                else:
                    st.session_state[
                        "search_results"
                    ].extend(
                        new_results
                    )

                st.session_state[
                    "search_candidate_offset"
                ] = (
                    more_package[
                        "next_offset"
                    ]
                )

                st.session_state[
                    "search_time_filter"
                ] = (
                    more_package.get(
                        "time_filter"
                    )
                )

                st.rerun()

            except Exception as error:
                st.error(
                    f"Další hledání selhalo: {error}"
                )

    elif query_used:
        st.info(
            "Pro tento dotaz nebyly nalezeny "
            "žádné relevantní e-maily."
        )

    st.divider()

    with st.expander(
        "🧠 Co si asistent pamatuje"
    ):
        aliases = get_search_aliases()

        if not aliases:
            st.caption(
                "Zatím nejsou uložené "
                "žádné známé osoby nebo pojmy."
            )

        else:
            for alias in aliases:
                alias_col1, alias_col2 = (
                    st.columns(
                        [5, 1]
                    )
                )

                with alias_col1:
                    st.write(
                        (
                            f"**{alias['alias']}** → "
                            f"{alias['sender_name'] or alias['sender_email']} "
                            f"({alias['sender_email']})"
                        )
                    )

                with alias_col2:
                    if st.button(
                        "🗑",
                        key=(
                            f"delete_alias_"
                            f"{alias['id']}"
                        ),
                        use_container_width=True,
                    ):
                        delete_search_alias(
                            alias[
                                "id"
                            ]
                        )

                        st.rerun()

    st.divider()

    st.markdown(
        "#### 📚 Index e-mailů"
    )

    current_stats = (
        get_search_index_stats()
    )

    st.caption(
        f"Aktuálně indexováno: "
        f"{current_stats['count']} e-mailů."
    )

    st.caption(
        "Již indexované zprávy se automaticky "
        "přeskočí. Opakovaná aktualizace doplní "
        "pouze nové e-maily."
    )

    period_options = {
        "Poslední měsíc":
            "month",

        "Posledních 6 měsíců":
            "6months",

        "Poslední rok":
            "year",

        "Poslední 2 roky":
            "2years",

        "Celá schránka":
            "all",
    }

    index_col1, index_col2 = (
        st.columns(
            [2, 1]
        )
    )

    with index_col1:
        selected_period_label = (
            st.selectbox(
                "Indexovat období",
                options=list(
                    period_options.keys()
                ),
                index=0,
                key="index_period",
            )
        )

    with index_col2:
        st.write("")
        st.write("")

        index_button = st.button(
            "📚 Aktualizovat index",
            use_container_width=True,
            key="index_button",
        )

    selected_period = (
        period_options[
            selected_period_label
        ]
    )

    if (
        index_button
        and selected_period
        == "all"
    ):
        st.session_state[
            "confirm_full_index"
        ] = True

        st.rerun()

    elif index_button:
        try:
            with st.spinner(
                "Kontroluji Gmail a doplňuji "
                "chybějící e-maily do indexu..."
            ):
                result = index_gmail_period(
                    period=selected_period
                )

            st.success(
                "Index byl aktualizován."
            )

            st.caption(
                (
                    f"Zkontrolováno: "
                    f"{result['checked']} · "
                    f"Již indexováno: "
                    f"{result['already_indexed']} · "
                    f"Nově přidáno: "
                    f"{result['added']} · "
                    f"Celkem v indexu: "
                    f"{result['total_indexed']}"
                )
            )

        except Exception as error:
            st.error(
                f"Indexování selhalo: {error}"
            )

    if st.session_state[
        "confirm_full_index"
    ]:
        st.warning(
            "⚠️ Opravdu chceš indexovat "
            "celou dostupnou historii Gmailu? "
            "Již indexované zprávy se znovu "
            "zpracovávat nebudou."
        )

        confirm_col, cancel_col = (
            st.columns(
                [1, 1]
            )
        )

        with confirm_col:
            if st.button(
                "✅ Ano, celou schránku",
                type="primary",
                use_container_width=True,
                key="confirm_full_index_button",
            ):
                st.session_state[
                    "confirm_full_index"
                ] = False

                try:
                    with st.spinner(
                        "Kontroluji celou schránku. "
                        "Tohle může chvíli trvat..."
                    ):
                        result = (
                            index_gmail_period(
                                period="all"
                            )
                        )

                    st.success(
                        "Index celé schránky byl aktualizován."
                    )

                    st.caption(
                        (
                            f"Zkontrolováno: "
                            f"{result['checked']} · "
                            f"Již indexováno: "
                            f"{result['already_indexed']} · "
                            f"Nově přidáno: "
                            f"{result['added']} · "
                            f"Celkem v indexu: "
                            f"{result['total_indexed']}"
                        )
                    )

                except Exception as error:
                    st.error(
                        f"Indexování selhalo: {error}"
                    )

        with cancel_col:
            if st.button(
                "Zrušit",
                use_container_width=True,
                key="cancel_full_index_button",
            ):
                st.session_state[
                    "confirm_full_index"
                ] = False

                st.rerun()

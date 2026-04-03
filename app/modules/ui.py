import streamlit as st
from textwrap import dedent


THEMES = {
    "Light": {
        "background": "#f4f7fb",
        "surface": "rgba(255, 255, 255, 0.88)",
        "surface_alt": "#ffffff",
        "text": "#14213d",
        "muted": "#52627a",
        "border": "rgba(20, 33, 61, 0.10)",
        "accent": "#0f6cbd",
        "accent_alt": "#f4a300",
        "shadow": "0 18px 40px rgba(16, 34, 68, 0.10)",
        "hero": "linear-gradient(135deg, #112a46 0%, #175676 48%, #f4a300 100%)",
    },
    "Dark": {
        "background": "#09111f",
        "surface": "rgba(17, 25, 40, 0.88)",
        "surface_alt": "#111b2d",
        "text": "#ecf3ff",
        "muted": "#9bb0cf",
        "border": "rgba(160, 190, 255, 0.16)",
        "accent": "#66b3ff",
        "accent_alt": "#ffbf47",
        "shadow": "0 18px 40px rgba(0, 0, 0, 0.35)",
        "hero": "linear-gradient(135deg, #081423 0%, #123456 48%, #8a5b00 100%)",
    },
}


def ensure_theme_state():
    st.session_state.ui_theme = "Light"
    return THEMES["Light"]


def render_theme_toggle():
    ensure_theme_state()
    choice = st.selectbox(
        "Appearance",
        options=list(THEMES.keys()),
        key="ui_theme",
        help="Switch between light and dark mode.",
    )
    return THEMES[choice]


def apply_theme(page_title: str, page_caption: str = ""):
    theme = ensure_theme_state()
    st.markdown(
        dedent(
            f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=DM+Sans:wght@400;500;700&display=swap');

        :root {{
            --app-bg: {theme["background"]};
            --app-surface: {theme["surface"]};
            --app-surface-alt: {theme["surface_alt"]};
            --app-text: {theme["text"]};
            --app-muted: {theme["muted"]};
            --app-border: {theme["border"]};
            --app-accent: {theme["accent"]};
            --app-accent-alt: {theme["accent_alt"]};
            --app-shadow: {theme["shadow"]};
            --app-hero: {theme["hero"]};
            --app-content-max: 1180px;
        }}

        html, body, [class*="css"]  {{
            font-family: "DM Sans", sans-serif;
        }}

        [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(circle at top right, rgba(244, 163, 0, 0.14), transparent 26%),
                radial-gradient(circle at top left, rgba(15, 108, 189, 0.16), transparent 32%),
                var(--app-bg);
            color: var(--app-text);
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--app-surface-alt) 0%, var(--app-surface) 100%);
            border-right: 1px solid var(--app-border);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        .block-container {{
            max-width: var(--app-content-max);
            margin: 0 auto;
            padding-top: 1.15rem;
            padding-bottom: 2.25rem;
        }}

        h1, h2, h3, h4 {{
            font-family: "Space Grotesk", sans-serif;
            color: var(--app-text);
            letter-spacing: -0.02em;
        }}

        h1 {{
            font-size: clamp(1.6rem, 3.2vw, 2.35rem);
            line-height: 1.1;
        }}

        h2 {{
            font-size: clamp(1.28rem, 2.2vw, 1.72rem);
            margin-top: 1.25rem;
        }}

        h3 {{
            font-size: clamp(1.04rem, 1.7vw, 1.3rem);
            margin-top: 0.95rem;
        }}

        p, li, label {{
            color: var(--app-text);
        }}

        [data-testid="stMetric"],
        [data-testid="stForm"],
        [data-testid="stDataFrame"],
        [data-testid="stAlert"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: 18px;
            box-shadow: var(--app-shadow);
        }}

        [data-testid="stSelectbox"],
        [data-testid="stTextInput"],
        [data-testid="stNumberInput"],
        [data-testid="stRadio"] {{
            background: transparent;
            border: 0;
            box-shadow: none;
        }}

        [data-testid="stMetric"] {{
            padding: 0.78rem 0.95rem;
        }}

        [data-testid="stForm"] {{
            padding: 1.15rem;
        }}

        [data-testid="stHorizontalBlock"] {{
            gap: 0.95rem;
        }}

        [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] {{
            gap: 0.7rem;
        }}

        button[kind="primary"], .stButton > button {{
            border-radius: 999px;
            border: 1px solid transparent;
            background: linear-gradient(135deg, var(--app-accent) 0%, var(--app-accent-alt) 100%);
            color: white;
            font-weight: 700;
        }}

        .app-hero {{
            padding: 1.3rem 1.35rem;
            border-radius: 24px;
            background: var(--app-hero);
            color: #ffffff;
            box-shadow: var(--app-shadow);
            border: 1px solid rgba(255, 255, 255, 0.14);
            margin-bottom: 1.25rem;
        }}

        .app-hero p {{
            color: rgba(255, 255, 255, 0.88);
            margin: 0.48rem 0 0 0;
            line-height: 1.6;
            max-width: 72ch;
        }}

        .app-card {{
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: 22px;
            padding: 1.03rem 1.08rem;
            box-shadow: var(--app-shadow);
        }}

        .app-card h4 {{
            margin: 0 0 0.35rem 0;
        }}

        .app-card p {{
            margin: 0;
            color: var(--app-muted);
            line-height: 1.55;
        }}

        .app-pill {{
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            color: white;
            font-size: 0.86rem;
            margin-bottom: 0.65rem;
        }}

        .rank-card {{
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: 24px;
            padding: 1.2rem;
            box-shadow: var(--app-shadow);
            text-align: center;
            min-height: 210px;
        }}

        .rank-score {{
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--app-accent);
            line-height: 1;
            margin-top: 0.75rem;
        }}

        .list-card {{
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: 18px;
            padding: 0.88rem 0.95rem;
            box-shadow: var(--app-shadow);
            margin-bottom: 0.68rem;
        }}

        .list-card .meta {{
            color: var(--app-muted);
            font-size: 0.95rem;
        }}

        @media (max-width: 900px) {{
            .block-container {{
                padding-top: 0.8rem;
            }}

            .app-hero {{
                border-radius: 18px;
                padding: 1rem 0.95rem;
                margin-bottom: 1rem;
            }}

            .app-card, .rank-card, .list-card {{
                border-radius: 14px;
            }}
        }}
        </style>
        """
        ),
        unsafe_allow_html=True,
    )

    if page_title:
        render_page_header(page_title, page_caption)


def render_page_header(title: str, caption: str = "", eyebrow: str = ""):
    eyebrow_html = f'<div class="app-pill">{eyebrow}</div>' if eyebrow else ""
    caption_html = f"<p>{caption}</p>" if caption else ""
    st.markdown(
        dedent(
            f"""
        <div class="app-hero">
            {eyebrow_html}
            <h1 style="margin:0;">{title}</h1>
            {caption_html}
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def render_info_card(title: str, body: str):
    st.markdown(
        dedent(
            f"""
        <div class="app-card">
            <h4>{title}</h4>
            <p>{body}</p>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def render_rank_card(
    place: str, trophy: str, name: str, score: str, subtitle: str = ""
):
    subtitle_html = (
        f'<div style="margin-top:0.45rem;color:var(--app-muted);">{subtitle}</div>'
        if subtitle
        else ""
    )
    st.markdown(
        dedent(
            f"""
        <div class="rank-card">
            <div style="font-size:2rem;">{trophy}</div>
            <div style="margin-top:0.5rem;color:var(--app-muted);font-weight:700;">{place}</div>
            <h3 style="margin:0.45rem 0 0 0;">{name}</h3>
            <div class="rank-score">{score}</div>
            {subtitle_html}
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def render_list_card(title: str, value: str, meta: str = ""):
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""
    st.markdown(
        dedent(
            f"""
        <div class="list-card">
            <div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;">
                <div>
                    <div style="font-weight:700;">{title}</div>
                    {meta_html}
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.35rem;font-weight:700;color:var(--app-accent);">{value}</div>
            </div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )

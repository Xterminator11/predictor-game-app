import json
import os
import socket
import datetime as dt
import boto3
from typing import Any
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import botocore
from modules.navigator import Navbar
from modules.ui import (
    apply_theme,
    render_info_card,
    render_list_card,
    render_page_header,
)

from modules.util_app import get_bucket_name, get_match_details_json

BUCKET_NAME = get_bucket_name()
st.suspend = False
st.ipl_completed = False

st.session_state.json_metadata = json.loads(
    open(
        os.path.join(os.path.dirname(__file__), "metadata.json"), "r", encoding="utf-8"
    ).read()
)

st.session_state.selected_match = st.session_state.get("selected_match", None)
Navbar()
apply_theme("", "")


def _get_query_match_id():
    match_id = st.query_params.get("match", None)
    if match_id is None or str(match_id) == "":
        return None
    return str(match_id)


def _set_query_match_id(match_id):
    if match_id is None:
        if "match" in st.query_params:
            del st.query_params["match"]
    else:
        st.query_params["match"] = str(match_id)


def login_screen():
    st.header("Welcome to Predictor App for IPL 2026")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)


def render_help_shortcut():
    st.markdown(
        """
        <style>
        .help-shortcut-link {
            display: block;
            text-decoration: none !important;
            color: inherit;
        }
        .help-shortcut-link:hover { text-decoration: none !important; color: inherit; }
        .help-shortcut-link * { text-decoration: none !important; }
        .help-shortcut-card {
            position: relative;
            overflow: hidden;
            background: linear-gradient(155deg, #ffffff 0%, #f9fbff 100%);
            border: 1px solid rgba(15, 108, 189, 0.18);
            border-radius: 20px;
            padding: 1.1rem 1.15rem;
            box-shadow: 0 14px 28px rgba(16, 34, 68, 0.08);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            cursor: pointer;
        }
        .help-shortcut-card::before {
            content: "";
            position: absolute;
            top: -36px;
            right: -28px;
            width: 120px;
            height: 120px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(244, 163, 0, 0.30) 0%, rgba(244, 163, 0, 0) 70%);
            pointer-events: none;
        }
        .help-shortcut-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 22px 38px rgba(16, 34, 68, 0.14);
            border-color: rgba(15, 108, 189, 0.42);
        }
        .help-shortcut-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.7rem;
            margin-bottom: 0.5rem;
        }
        .help-shortcut-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border-radius: 999px;
            background: linear-gradient(135deg, #0f6cbd 0%, #f4a300 100%);
            color: #ffffff;
            font-size: 0.95rem;
            font-weight: 700;
        }
        .help-shortcut-title {
            margin: 0;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--app-text);
            letter-spacing: -0.01em;
        }
        .help-shortcut-body {
            margin: 0;
            color: var(--app-muted);
            line-height: 1.58;
            font-size: 0.95rem;
        }
        .help-shortcut-cta {
            margin-top: 0.78rem;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            color: #0f6cbd;
            font-weight: 700;
            font-size: 0.94rem;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: rgba(15, 108, 189, 0.09);
        }
        </style>
        <a class="help-shortcut-link" href="./help">
            <div class="help-shortcut-card">
                <div class="help-shortcut-top">
                    <div class="help-shortcut-title">Need the rules?</div>
                    <div class="help-shortcut-badge">?</div>
                </div>
                <p class="help-shortcut-body">Open the Help page for navigation steps, point-system details, booster examples, and strategy tips.</p>
                <div class="help-shortcut-cta">Open Help and Rules <span>&rarr;</span></div>
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )


def multi_select_check_1():
    if st.session_state.booster_2 or st.session_state.booster_3:
        st.session_state.booster_2 = False
        st.session_state.booster_3 = False


def multi_select_check_2():
    if st.session_state.booster_1 or st.session_state.booster_3:
        st.session_state.booster_1 = False
        st.session_state.booster_3 = False


def multi_select_check_3():
    if st.session_state.booster_2 or st.session_state.booster_1:
        st.session_state.booster_2 = False
        st.session_state.booster_1 = False


def get_booster_data_file(match_id):

    # 1.⁠ ⁠Game 1 to Game 20
    # 2.⁠ ⁠⁠Game 21 to Game 40
    # 3.⁠ ⁠⁠Game 41 to Game 60
    # 4.⁠ ⁠⁠Game 61 to Game 70
    # 5.⁠ ⁠⁠Game 71 to Game 74

    if 0 <= match_id <= 20:
        return "match_booster.json"
    elif 21 <= match_id <= 40:
        return "match_booster_1.json"
    elif 41 <= match_id <= 60:
        return "match_booster_2.json"
    elif 61 <= match_id <= 70:
        return "match_booster_3.json"
    elif 71 <= match_id <= 74:
        return "match_booster_4.json"


def get_booster_information(match_details=None):

    if match_details is None:
        match_details = st.session_state.selected_match

    if not match_details:
        return False, False, False, {}

    user_name = str(st.session_state.user_name).replace(" ", "").lower()
    match_id = match_details.get("MatchNumber")

    booster_data_found = False
    s3object = f"{user_name}/{get_booster_data_file(match_id)}"
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=s3object)
        booster_data_found = True
    except botocore.exceptions.ClientError:
        booster_data_found = False

    booster_1 = False
    booster_2 = False
    booster_3 = False

    if booster_data_found is False:
        booster_data = {"booster_1": 0, "booster_2": 0, "booster_3": 0}
    else:
        data = s3.get_object(Bucket=BUCKET_NAME, Key=s3object)
        booster_data = json.loads(data["Body"].read().decode("utf-8"))
        booster_1 = True if booster_data.get("booster_1") > 0 else False
        booster_2 = True if booster_data.get("booster_2") > 0 else False
        booster_3 = True if booster_data.get("booster_3") > 0 else False

    return booster_1, booster_2, booster_3, booster_data


def store_booster_information(match_details=None):

    if match_details is None:
        match_details = st.session_state.selected_match

    if not match_details:
        return False, False, False, {}

    user_name = str(st.session_state.user_name).replace(" ", "").lower()
    match_id = match_details.get("MatchNumber")

    _booster_1, _booster_2, _booster_3, booster_data = get_booster_information(
        match_details
    )

    if st.session_state.booster_1 is True:
        booster_data["booster_1"] = match_id

    if st.session_state.booster_2 is True:
        booster_data["booster_2"] = match_id

    if st.session_state.booster_3 is True:
        booster_data["booster_3"] = match_id

    s3object = f"{user_name}/{get_booster_data_file(match_id)}"

    s3 = boto3.resource("s3")
    s3object = s3.Object(BUCKET_NAME, s3object)
    s3object.put(Body=(bytes(json.dumps(booster_data).encode("UTF-8"))))


def clear_booster_details(match_details=None):

    if match_details is None:
        match_details = st.session_state.selected_match

    if not match_details:
        return False, False, False, {}

    user_name = str(st.session_state.user_name).replace(" ", "").lower()
    match_id = match_details.get("MatchNumber")

    _booster_1, _booster_2, _booster_3, booster_data = get_booster_information(
        match_details
    )

    for booster_keys in booster_data.keys():
        if booster_data.get(booster_keys) == match_id:
            booster_data[booster_keys] = 0

    s3object = f"{user_name}/{get_booster_data_file(match_id)}"

    s3 = boto3.resource("s3")
    s3object = s3.Object(BUCKET_NAME, s3object)
    s3object.put(Body=(bytes(json.dumps(booster_data).encode("UTF-8"))))


def store_data_values():

    match_details = st.session_state.current_match

    user_name = str(st.session_state.user_name).replace(" ", "").lower()
    match_id = match_details.get("MatchNumber")
    json_data = {
        "UserName": user_name,
        "MatchId": match_id,
        "MatchTime": str(match_details.get("DateUtc")),
        "SubmitTime": datetime.now(tz=dt.timezone.utc).strftime(
            format="%Y-%m-%d %H:%M:%S"
        ),
    }
    selections = []
    for question in st.session_state.json_metadata.get("question_list"):
        selections.append(
            {
                "q_key": question.get("q_key"),
                "q_val": st.session_state.get(question.get("q_key")),
            }
        )
    json_data["Selections"] = selections
    s3object = f"{user_name}/{user_name}_{match_id}.json"

    s3 = boto3.resource("s3")
    s3object = s3.Object(BUCKET_NAME, s3object)

    s3object.put(Body=(bytes(json.dumps(json_data).encode("UTF-8"))))

    # Store Booster Data

    store_booster_information(match_details)

    st.session_state.selected_match = None
    _set_query_match_id(None)
    st.success("Predictions submitted successfully!")
    st.rerun()


def get_next_match_from_json() -> list:

    match_details_json = get_match_details_json(data_type="pandas")

    data_frame = pd.read_json(
        match_details_json,
        orient="records",
        convert_dates=["DateUtc"],
    )

    current_time = pd.Timestamp.now(tz=dt.timezone.utc)
    # Filter Data Frame Now

    data_frame = data_frame[data_frame["DateUtc"] > current_time.to_datetime64()]

    data_frame = data_frame[
        data_frame["MatchNumber"] == data_frame["MatchNumber"].min()
    ]

    if len(data_frame) == 0:
        return []
    return data_frame.fillna("").to_json(
        orient="records", date_format="iso", date_unit="s"
    )


def _safe_int(value: Any):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _average(values: list[int]):
    return round(sum(values) / len(values), 1) if values else None


def get_recent_team_insights(match_details: dict, games_limit: int = 5) -> dict:
    match_details_json = get_match_details_json(data_type="json")
    data_frame = pd.read_json(
        match_details_json,
        orient="records",
        convert_dates=["DateUtc"],
    )

    if data_frame.empty:
        return {}

    data_frame["DateUtc"] = pd.to_datetime(
        data_frame["DateUtc"], errors="coerce", utc=True
    )
    current_match_time = pd.to_datetime(
        match_details.get("DateUtc"), errors="coerce", utc=True
    )

    if pd.isna(current_match_time):
        current_match_time = pd.Timestamp.now(tz=dt.timezone.utc)

    completed_matches = data_frame[
        (data_frame["ResultsPublished"].fillna(False))
        & (data_frame["MatchCompletionStatus"] == "Completed")
        & (data_frame["DateUtc"] < current_match_time)
    ]

    home_team = match_details.get("HomeTeam")
    away_team = match_details.get("AwayTeam")

    def build_team_summary(team_name: str):
        team_matches = completed_matches[
            (completed_matches["HomeTeam"] == team_name)
            | (completed_matches["AwayTeam"] == team_name)
        ].sort_values("DateUtc", ascending=False)

        if team_matches.empty:
            return {
                "count": 0,
                "results": [],
                "totalscore": [],
                "fours": [],
                "sixes": [],
                "powerplay": [],
                "dotballs": [],
                "highest_over_score": [],
                "wickets": [],
                "avg": {},
            }

        team_matches = team_matches.head(games_limit).iloc[::-1]

        results = []
        totalscore = []
        fours = []
        sixes = []
        powerplay = []
        dotballs = []
        highest_over_score = []
        wickets = []

        for _, row in team_matches.iterrows():
            stats = row.get("ResultsStats")
            if not isinstance(stats, dict):
                continue

            prefix = "HomeTeam" if row.get("HomeTeam") == team_name else "AwayTeam"
            opp_prefix = "AwayTeam" if prefix == "HomeTeam" else "HomeTeam"

            winner_value = str(stats.get(f"{prefix}_winner", "")).lower()
            if winner_value == "won":
                results.append("W")
            elif winner_value == "lost":
                results.append("L")
            else:
                results.append("N")

            totalscore_value = _safe_int(stats.get(f"{prefix}_totalscore"))
            fours_value = _safe_int(stats.get(f"{prefix}_fours"))
            sixes_value = _safe_int(stats.get(f"{prefix}_sixes"))
            powerplay_value = _safe_int(stats.get(f"{prefix}_powerplay"))
            dotballs_value = _safe_int(stats.get(f"{prefix}_dotballs"))
            highest_over_score_value = _safe_int(
                stats.get(f"{prefix}_highest_over_score")
            )
            wickets_value = _safe_int(stats.get(f"{prefix}_wickets"))

            opp_totalscore = _safe_int(stats.get(f"{opp_prefix}_totalscore"))
            opp_fours = _safe_int(stats.get(f"{opp_prefix}_fours"))
            opp_sixes = _safe_int(stats.get(f"{opp_prefix}_sixes"))
            opp_powerplay = _safe_int(stats.get(f"{opp_prefix}_powerplay"))
            opp_dotballs = _safe_int(stats.get(f"{opp_prefix}_dotballs"))
            opp_highest = _safe_int(stats.get(f"{opp_prefix}_highest_over_score"))
            opp_wickets = _safe_int(stats.get(f"{opp_prefix}_wickets"))

            if totalscore_value is not None:
                totalscore.append((totalscore_value, opp_totalscore))
            if fours_value is not None:
                fours.append((fours_value, opp_fours))
            if sixes_value is not None:
                sixes.append((sixes_value, opp_sixes))
            if powerplay_value is not None:
                powerplay.append((powerplay_value, opp_powerplay))
            if dotballs_value is not None:
                dotballs.append((dotballs_value, opp_dotballs))
            if highest_over_score_value is not None:
                highest_over_score.append((highest_over_score_value, opp_highest))
            if wickets_value is not None:
                wickets.append((opp_wickets, wickets_value))

        def _vals(pairs):
            return [p[0] for p in pairs]

        return {
            "count": len(team_matches),
            "results": results,
            "totalscore": totalscore,
            "fours": fours,
            "sixes": sixes,
            "powerplay": powerplay,
            "dotballs": dotballs,
            "highest_over_score": highest_over_score,
            "wickets": wickets,
            "avg": {
                "totalscore": _average(_vals(totalscore)),
                "fours": _average(_vals(fours)),
                "sixes": _average(_vals(sixes)),
                "powerplay": _average(_vals(powerplay)),
                "dotballs": _average(_vals(dotballs)),
                "highest_over_score": _average(_vals(highest_over_score)),
                "wickets": _average(_vals(wickets)),
            },
        }

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home": build_team_summary(home_team),
        "away": build_team_summary(away_team),
    }


def _values_to_text(values: list[int]):
    return " | ".join(str(value) for value in values) if values else "N/A"


def _render_stat_chips(pairs: list[tuple], higher_is_better: bool = True):
    if not pairs:
        return '<span class="stat-chip">N/A</span>'
    chips = []
    for pair in pairs:
        if isinstance(pair, tuple) and len(pair) == 2:
            val, opp = pair
            if opp is None:
                css = "stat-chip"
            elif val > opp:
                css = "stat-chip-win" if higher_is_better else "stat-chip-loss"
            elif val < opp:
                css = "stat-chip-loss" if higher_is_better else "stat-chip-win"
            else:
                css = "stat-chip-tie"
        else:
            val = pair
            css = "stat-chip"
        chips.append(f'<span class="stat-chip {css}">{val}</span>')
    return "".join(chips)


def _format_average(value: float | None):
    return f"{value:.1f}" if value is not None else "N/A"


def _render_result_chips(results: list[str]):
    if not results:
        return '<span class="result-chip result-chip-neutral">N/A</span>'

    chip_html = []
    for result in results:
        css_class = (
            "result-chip-win"
            if result == "W"
            else "result-chip-loss"
            if result == "L"
            else "result-chip-neutral"
        )
        chip_html.append(f'<span class="result-chip {css_class}">{result}</span>')
    return "".join(chip_html)


def _render_stat_label(q_key: str):
    labels = {
        "winner": "Last 5 Results",
        "fours": "Fours (Last 5)",
        "sixes": "Sixes (Last 5)",
        "wickets": "Wickets Taken (Last 5)",
        "powerplay": "Powerplay Runs (Last 5)",
        "dotballs": "Dot Balls (Last 5)",
        "highest_over_score": "Best Over (Last 5)",
        "totalscore": "Total Runs (Last 5)",
    }
    return labels.get(q_key, "Last 5")


def get_question_insight_html(
    q_key: str,
    home_team: str,
    away_team: str,
    home: dict,
    away: dict,
):
    label = _render_stat_label(q_key)

    if q_key == "winner":
        return f"""
        <div class="team-form-card">
            <div class="team-form-title">{home_team}</div>
            <div>{_render_result_chips(home.get("results", []))}</div>
            <div class="team-form-meta">{label}</div>
        </div>
        <div class="team-form-card" style="margin-top:0.55rem;">
            <div class="team-form-title">{away_team}</div>
            <div>{_render_result_chips(away.get("results", []))}</div>
            <div class="team-form-meta">{label}</div>
        </div>
        """

    metric_map = {
        "fours": "fours",
        "sixes": "sixes",
        "wickets": "wickets",
        "powerplay": "powerplay",
        "dotballs": "dotballs",
        "highest_over_score": "highest_over_score",
        "totalscore": "totalscore",
    }

    metric_key = metric_map.get(q_key)
    if not metric_key:
        return ""

    home_vals = home.get(metric_key, [])
    away_vals = away.get(metric_key, [])
    home_avg = home.get("avg", {}).get(metric_key)
    away_avg = away.get("avg", {}).get(metric_key)
    higher_better = metric_key not in ["dotballs"]

    return f"""
    <div class="team-form-card">
        <div class="team-form-title">{home_team}</div>
        <div>{_render_stat_chips(home_vals, higher_better)}</div>
        <div class="team-form-meta">Avg: {_format_average(home_avg)} &middot; {label}</div>
    </div>
    <div class="team-form-card" style="margin-top:0.55rem;">
        <div class="team-form-title">{away_team}</div>
        <div>{_render_stat_chips(away_vals, higher_better)}</div>
        <div class="team-form-meta">Avg: {_format_average(away_avg)} &middot; {label}</div>
    </div>
    """


def body_rendering(match_details=None):
    if not match_details:
        return

    match_date = pd.to_datetime(match_details.get("DateUtc"), errors="coerce")
    date_display = (
        match_date.strftime("%d %b %Y, %I:%M %p UTC")
        if pd.notna(match_date)
        else str(match_details.get("DateUtc", "TBD"))
    )
    left, middle, right = st.columns(
        [1.2, 1, 1.2], border=True, vertical_alignment="center"
    )

    st.markdown(
        """
        <style>
        .match-details-card {
            border: 1px solid var(--app-border);
            border-radius: 16px;
            background: var(--app-surface);
            box-shadow: var(--app-shadow);
            padding: 0.95rem 0.9rem;
            text-align: center;
        }
        .match-details-label {
            color: var(--app-muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.15rem;
        }
        .match-details-value {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.58rem;
            color: var(--app-text);
        }
        .match-details-value:last-child {
            margin-bottom: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left.image(
        st.session_state.json_metadata.get("teams_image").get(
            match_details.get("HomeTeam")
        )
    )
    left.markdown(f"### {match_details.get('HomeTeam')}")

    right.image(
        st.session_state.json_metadata.get("teams_image").get(
            match_details.get("AwayTeam")
        )
    )
    right.markdown(f"### {match_details.get('AwayTeam')}")

    middle.markdown(
        f"""
        <div class="match-details-card">
            <div class="match-details-label">Match Number</div>
            <div class="match-details-value">{match_details.get("MatchNumber")}</div>
            <div class="match-details-label">Date</div>
            <div class="match-details-value">{date_display}</div>
            <div class="match-details-label">Venue</div>
            <div class="match-details-value">{match_details.get("Location")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def form_rendering(match_details):

    st.session_state.current_match = match_details

    insight_data = get_recent_team_insights(match_details)

    home_team = match_details.get("HomeTeam")
    away_team = match_details.get("AwayTeam")
    home_insights = insight_data.get("home", {})
    away_insights = insight_data.get("away", {})

    # ── Shared CSS for prediction cards ──
    st.markdown(
        """
        <style>
        .team-form-card {
            border: 1px solid var(--app-border);
            border-radius: 16px;
            background: var(--app-surface);
            box-shadow: var(--app-shadow);
            padding: 0.82rem 0.88rem;
        }
        .team-form-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .result-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.1rem;
            height: 2.1rem;
            border-radius: 999px;
            font-weight: 700;
            margin-right: 0.3rem;
            border: 1px solid transparent;
            font-size: 0.85rem;
        }
        .result-chip-win {
            background: rgba(25, 135, 84, 0.16);
            color: #198754;
            border-color: rgba(25, 135, 84, 0.34);
        }
        .result-chip-loss {
            background: rgba(220, 53, 69, 0.12);
            color: #dc3545;
            border-color: rgba(220, 53, 69, 0.28);
        }
        .result-chip-neutral {
            background: rgba(108, 117, 125, 0.15);
            color: #6c757d;
            border-color: rgba(108, 117, 125, 0.3);
        }
        .team-form-meta {
            color: var(--app-muted);
            margin-top: 0.38rem;
            font-size: 0.84rem;
        }
        .stat-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2.1rem;
            height: 2.1rem;
            border-radius: 999px;
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
            font-size: 0.85rem;
            margin-right: 0.3rem;
            margin-bottom: 0.2rem;
            padding: 0 0.45rem;
            background: rgba(15, 108, 189, 0.12);
            color: #0f6cbd;
            border: 1px solid rgba(15, 108, 189, 0.28);
        }
        .stat-chip-win {
            background: rgba(25, 135, 84, 0.16);
            color: #198754;
            border-color: rgba(25, 135, 84, 0.34);
        }
        .stat-chip-loss {
            background: rgba(220, 53, 69, 0.12);
            color: #dc3545;
            border-color: rgba(220, 53, 69, 0.28);
        }
        .stat-chip-tie {
            background: rgba(255, 193, 7, 0.16);
            color: #b8860b;
            border-color: rgba(255, 193, 7, 0.38);
        }
        .question-card-title {
            margin-bottom: 0.05rem;
        }
        .question-card-points {
            color: var(--app-muted);
            font-size: 0.88rem;
            margin-bottom: 0.35rem;
        }
        .booster-card-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }
        .booster-card-desc {
            color: var(--app-muted);
            font-size: 0.88rem;
        }
        </style>
        <style>
        /* Orange toggle for booster switches */
        [data-testid="stToggle"] label > div[data-testid="stToggleSwitch"] > div {
            background-color: rgba(244, 163, 0, 0.4) !important;
            border-radius: 999px !important;
        }
        [data-testid="stToggle"] label > div[data-testid="stToggleSwitch"] > div[aria-checked="true"] {
            background-color: #f4a300 !important;
        }
        [data-testid="stToggle"] label > div[data-testid="stToggleSwitch"] > div > div {
            background-color: #fff !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
        }
        [data-testid="stToggle"] label > span {
            font-weight: 700 !important;
            font-size: 0.95rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            "<div class='booster-card-title'>Select Booster for this match</div>"
            "<div class='booster-card-desc'>Pick one booster to multiply your score for this fixture</div>",
            unsafe_allow_html=True,
        )

        booster_5x, booster_3x, booster_2x, booster_data = get_booster_information()

        booster_1, booster_2, booster_3 = st.columns(3)

        with booster_1:
            st.toggle(
                "5x Booster 🔥🔥🔥🔥🔥",
                disabled=booster_5x,
                label_visibility="visible",
                help=(
                    "5X of your total score"
                    if booster_5x is False
                    else f"Booster was used in match number {booster_data.get('booster_1')}"
                ),
                key="booster_1",
                on_change=multi_select_check_1,
            )

        with booster_2:
            st.toggle(
                "3x Booster 🔥🔥🔥",
                disabled=booster_3x,
                label_visibility="visible",
                help=(
                    "3X of your total score"
                    if booster_3x is False
                    else f"Booster was used in match number {booster_data.get('booster_2')}"
                ),
                key="booster_2",
                on_change=multi_select_check_2,
            )

        with booster_3:
            st.toggle(
                "2x Booster 🔥🔥",
                disabled=booster_2x,
                label_visibility="visible",
                help=(
                    "2X of your total score"
                    if booster_2x is False
                    else f"Booster was used in match number {booster_data.get('booster_3')}"
                ),
                key="booster_3",
                on_change=multi_select_check_3,
            )

    st.subheader("Select Predictions for this match")
    for question in st.session_state.json_metadata.get("question_list"):
        with st.container(border=True):
            st.markdown(
                f"<div class='question-card-title'><strong>{question.get('questions')}</strong></div>"
                f"<div class='question-card-points'>{question.get('points')} points available</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                get_question_insight_html(
                    question.get("q_key"),
                    home_team,
                    away_team,
                    home_insights,
                    away_insights,
                ),
                unsafe_allow_html=True,
            )
            if question.get("display_type") == "radio":
                st.radio(
                    label="Your pick",
                    options=[home_team, away_team],
                    key=question.get("q_key"),
                    horizontal=True,
                )
            elif question.get("display_type") == "slider" and question.get("q_key") in [
                "totalscore"
            ]:
                st.slider(
                    label="Your total score prediction",
                    key=question.get("q_key"),
                    min_value=1,
                    max_value=600,
                )
            elif question.get("display_type") == "slider" and question.get("q_key") in [
                "highest_over_score"
            ]:
                st.slider(
                    label="Your highest over score prediction",
                    key=question.get("q_key"),
                    min_value=1,
                    max_value=45,
                )
            else:
                continue
    st.button("Submit Predictions", on_click=store_data_values, type="primary")


def check_match_date_selected():

    if len(st.session_state.next_matches) == 0:
        # st.subheader("No Matches to be played")
        return True
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]
        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        s3object = f"{user_name}/{user_name}_{match_id}.json"
        s3 = boto3.client("s3")
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=s3object)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                return True
        return True


def is_match_locked(match_id, user_name):
    user_name = str(user_name).replace(" ", "").lower()
    s3object = f"{user_name}/{user_name}_{match_id}.json"
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=s3object)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            return True


def get_next_matches(limit=7):
    match_details_json = get_match_details_json(data_type="json")
    data_frame = pd.read_json(
        match_details_json,
        orient="records",
        convert_dates=["DateUtc"],
    )
    data_frame["DateUtc"] = pd.to_datetime(
        data_frame["DateUtc"], utc=True, errors="coerce"
    )
    current_time = pd.Timestamp.now(tz=dt.timezone.utc)
    upcoming = (
        data_frame[(data_frame["DateUtc"] > current_time)]
        .sort_values("DateUtc")
        .head(limit)
    )
    return upcoming.to_dict("records")


def get_selected_match_by_id(match_id):
    if match_id is None:
        return None
    for match in get_next_matches(limit=100):
        if str(match.get("MatchNumber")) == str(match_id):
            return match
    return None


query_match_id = _get_query_match_id()
if query_match_id is not None:
    selected_match = get_selected_match_by_id(query_match_id)
    st.session_state.selected_match = selected_match
else:
    st.session_state.selected_match = None


def get_matches_in_range(start_date, end_date):
    match_details_json = get_match_details_json(data_type="json")
    data_frame = pd.read_json(
        match_details_json,
        orient="records",
        convert_dates=["DateUtc"],
    )
    data_frame["DateUtc"] = pd.to_datetime(
        data_frame["DateUtc"], utc=True, errors="coerce"
    )
    if not pd.api.types.is_datetime64tz_dtype(start_date):
        start_date = pd.Timestamp(start_date).tz_localize("UTC")
    if not pd.api.types.is_datetime64tz_dtype(end_date):
        end_date = pd.Timestamp(end_date).tz_localize("UTC")
    upcoming = data_frame[
        (data_frame["DateUtc"] >= start_date) & (data_frame["DateUtc"] <= end_date)
    ].sort_values("DateUtc")
    return upcoming.to_dict("records")


def show_match_cards():
    st.header("Select a Match to Predict")
    matches = get_next_matches()

    if not matches:
        st.subheader("No upcoming matches")
        return

    # global card styles for match listing
    st.markdown(
        """
        <style>
        .match-card-link {
            display: block;
            text-decoration: none !important;
            color: inherit;
            margin-bottom: 0.75rem;
        }
        .match-card-link:hover { color: inherit; text-decoration: none !important; }
        .match-card-link * { text-decoration: none !important; }
        .match-card {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            border: 1px solid rgba(15, 108, 189, 0.18);
            border-radius: 16px;
            padding: 1.1rem 1.4rem;
            background: linear-gradient(180deg, #ffffff 0%, #f7f9ff 100%);
            box-shadow: 0 8px 20px rgba(15, 108, 189, 0.07);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            cursor: pointer;
        }
        .match-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 16px 32px rgba(15, 108, 189, 0.13);
            border-color: rgba(15, 108, 189, 0.40);
        }
        .match-card-teams-section {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        .match-card .team-logo {
            width: 44px;
            height: 44px;
            object-fit: contain;
            border-radius: 10px;
            background: #ffffff;
            padding: 0.25rem;
            border: 1px solid rgba(15, 108, 189, 0.10);
            flex-shrink: 0;
        }
        .match-card .vs-label {
            font-weight: 600;
            font-size: 0.85rem;
            color: #5b6b8d;
            flex-shrink: 0;
        }
        .match-card .match-teams {
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
            font-size: 1rem;
            letter-spacing: -0.01em;
            text-align: center;
            word-break: break-word;
            hyphens: auto;
        }
        .match-card .match-meta {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            flex-wrap: wrap;
        }
        .match-card .match-date {
            color: #5b6b8d;
            font-size: 0.88rem;
            word-break: break-word;
        }
        .match-card .match-status {
            display: inline-flex;
            align-items: center;
            font-weight: 700;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            font-size: 0.82rem;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .match-card .match-status.locked {
            color: #1f7a32;
            background: rgba(25, 135, 84, 0.12);
        }
        .match-card .match-status.unlocked {
            color: #b02a37;
            background: rgba(220, 53, 69, 0.12);
        }
        .match-card .match-arrow {
            color: #0f6cbd;
            font-size: 1.2rem;
            font-weight: 700;
            flex-shrink: 0;
        }
        @media (min-width: 768px) {
            .match-card {
                flex-direction: row;
                align-items: center;
            }
            .match-card-teams-section {
                flex: 1;
                justify-content: flex-start;
            }
            .match-card .match-teams {
                text-align: left;
            }
            .match-card .match-meta {
                margin-left: auto;
                flex-shrink: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    for match in matches:
        home_logo = st.session_state.json_metadata.get("teams_image", {}).get(
            match["HomeTeam"], ""
        )
        away_logo = st.session_state.json_metadata.get("teams_image", {}).get(
            match["AwayTeam"], ""
        )
        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        locked = is_match_locked(match["MatchNumber"], user_name)
        status = "Locked" if locked else "Unlocked"
        status_class = "locked" if locked else "unlocked"
        match_date = pd.to_datetime(match["DateUtc"], errors="coerce")
        date_label = (
            match_date.strftime("%a, %d %b · %I:%M %p UTC")
            if pd.notna(match_date)
            else str(match["DateUtc"])
        )
        match_id = match["MatchNumber"]

        st.markdown(
            f"""
            <a class="match-card-link" href="?match={match_id}">
                <div class="match-card">
                    <div class="match-card-teams-section">
                        <img class="team-logo" src="{home_logo}" alt="{match["HomeTeam"]}" />
                        <span class="vs-label">vs</span>
                        <img class="team-logo" src="{away_logo}" alt="{match["AwayTeam"]}" />
                        <span class="match-teams">{match["HomeTeam"]} vs {match["AwayTeam"]}</span>
                    </div>
                    <div class="match-meta">
                        <span class="match-date">{date_label}</span>
                        <span class="match-status {status_class}">{status}</span>
                        <span class="match-arrow">&rarr;</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )


def show_main_page():
    if st.session_state.selected_match is None:
        show_match_cards()
    else:
        match = st.session_state.selected_match
        body_rendering(match)
        locked = is_match_locked(match["MatchNumber"], st.session_state.user_name)
        if locked:
            st.subheader(
                f"Your selections are locked for {match['HomeTeam']} vs {match['AwayTeam']}"
            )
            display_details_of_the_prediction(match)
            if st.button("Back to Matches"):
                st.session_state.selected_match = None
                _set_query_match_id(None)
                st.rerun()
        else:
            form_rendering(match)
            if st.button("Back to Matches"):
                st.session_state.selected_match = None
                _set_query_match_id(None)
                st.rerun()


def clear_selections(match_details):

    user_name = str(st.session_state.user_name).replace(" ", "").lower()
    match_id = match_details.get("MatchNumber")

    s3object = f"{user_name}/{user_name}_{match_id}.json"
    s3 = boto3.client("s3")
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3object)
        clear_booster_details()
        st.success("Selections cleared")
        st.rerun()  # to refresh the status
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            st.error("No selections to clear")
        else:
            st.error("Error clearing selections")


def display_details_of_the_prediction(match_details):

    user_name = str(st.session_state.user_name).replace(" ", "").lower()
    match_id = match_details.get("MatchNumber")

    s3object = f"{user_name}/{user_name}_{match_id}.json"
    s3 = boto3.client("s3")

    _booster_1, _booster_2, _booster_3, contents_booster = get_booster_information()
    try:
        data = s3.get_object(Bucket=BUCKET_NAME, Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))

        for booster in contents_booster.keys():
            if contents_booster.get(booster) == match_id:
                booster_details = (
                    "5x"
                    if booster == "booster_1"
                    else "3x"
                    if booster == "booster_2"
                    else "2x"
                )
                render_info_card(
                    "Booster Selected",
                    f"You used the {booster_details} booster for this match.",
                )

        for data_selections in contents.get("Selections"):
            for question in st.session_state.json_metadata.get("question_list"):
                if question.get("q_key") == data_selections.get("q_key"):
                    render_list_card(
                        question.get("questions"),
                        str(data_selections.get("q_val")),
                        f"{question.get('points')} point question",
                    )
                else:
                    continue

        st.button(
            "Do you want to clear all your selection?",
            key="clear",
            on_click=clear_selections,
            args=(match_details,),
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            st.error("No predictions found")
        else:
            st.error("Error loading predictions")


if st.suspend:
    st.header("Due to Operations Sindoor !! Prediction game is suspended")
elif st.ipl_completed:
    st.header("IPL Completed thanks for playing predictor game")
else:
    if socket.gethostname() == "MacBookPro.lan":
        st.session_state.user_name = "Gururaj Rao"
        st.session_state.next_matches = get_next_match_from_json()

        if json.loads(st.session_state.next_matches[0]).get("MatchNumber") == "75":
            st.header("IPL Is Done ! Thanks for Playing Predictor game!")
        else:
            render_page_header(
                f"Welcome, {st.session_state.user_name}!",
                "Lock in your predictions, time your boosters, and manage the next IPL fixture from one focused dashboard.",
                "Predictor Home Page",
            )
            render_help_shortcut()
            show_main_page()

            # Render Statistics

            st.button("Log out", on_click=st.logout)
    else:
        if not st.user.is_logged_in:
            login_screen()
        else:
            st.session_state.user_name = st.user.name
            st.session_state.next_matches = get_next_match_from_json()
            render_page_header(
                f"Welcome, {st.session_state.user_name}!",
                "Lock in your predictions, time your boosters, and manage the next IPL fixture from one focused dashboard.",
                "Predictor Home Page",
            )
            render_help_shortcut()
            show_main_page()
            ## Add Questions

            st.button("Log out", on_click=st.logout)

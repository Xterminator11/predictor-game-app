import streamlit as st
import json
import boto3
import os
import pandas as pd
from modules.navigator import Navbar
from modules.ui import (
    apply_theme,
    render_page_header,
)
import socket
import botocore
import datetime as dt
import html
from modules.util_app import get_bucket_name, get_match_details_json

BUCKET_NAME = get_bucket_name()

st.set_page_config(
    page_title="Predictor Statistics",
    page_icon="https://brandlogos.net/wp-content/uploads/2021/12/indian_premier_league-brandlogo.net_.png",
)

st.session_state.booster_value = 1

st.session_state.json_metadata = json.loads(
    open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.json"),
        "r",
        encoding="utf-8",
    ).read()
)

st.session_state.json_match = json.loads(get_match_details_json(data_type="json"))

Navbar()
apply_theme("", "")
render_page_header(
    "Statistics",
    "Review published match stats, compare your picks with actual results, and explore score and booster patterns across players.",
    "Match Intelligence",
)

st.markdown(
    """
    <style>
    .booster-strip {
        display: flex;
        gap: 0.6rem;
        margin: 0.25rem 0 0.6rem 0;
        flex-wrap: wrap;
    }
    .booster-pill {
        padding: 0.44rem 0.72rem;
        border-radius: 999px;
        border: 1px solid var(--app-border);
        font-weight: 700;
        font-size: 0.88rem;
        color: var(--app-muted);
        background: var(--app-surface-alt);
    }
    .booster-pill.active {
        color: #ffffff;
        border-color: transparent;
        background: linear-gradient(135deg, #ff8f1f 0%, #d9480f 100%);
    }
    .stat-compare-card {
        background: var(--app-surface);
        border: 1px solid var(--app-border);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        box-shadow: var(--app-shadow);
    }
    .stat-compare-card .title {
        font-weight: 700;
        margin-bottom: 0.45rem;
    }
    .value-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.65rem;
    }
    .value-chip {
        border-radius: 10px;
        padding: 0.45rem 0.55rem;
        font-size: 0.92rem;
        border: 1px solid transparent;
    }
    .value-chip.good {
        background: rgba(46, 160, 67, 0.16);
        color: #1f7a31;
        border-color: rgba(46, 160, 67, 0.35);
    }
    .value-chip.bad {
        background: rgba(220, 53, 69, 0.14);
        color: #a81628;
        border-color: rgba(220, 53, 69, 0.35);
    }
    .prediction-card {
        background: var(--app-surface);
        border: 1px solid var(--app-border);
        border-radius: 16px;
        padding: 0.92rem 1rem;
        box-shadow: var(--app-shadow);
        margin-bottom: 0.62rem;
    }
    .prediction-card.correct {
        border-left: 5px solid #2ea043;
    }
    .prediction-card.partial {
        border-left: 5px solid #d29922;
    }
    .prediction-card.unavailable {
        border-left: 5px solid #98a2b3;
        background: linear-gradient(180deg, rgba(152, 162, 179, 0.07) 0%, var(--app-surface) 100%);
    }
    .prediction-card.wrong {
        border-left: 5px solid #dc3545;
    }
    .prediction-status.correct {
        color: #2ea043;
        font-weight: 700;
    }
    .prediction-status.partial {
        color: #9a6700;
        font-weight: 700;
    }
    .prediction-status.unavailable {
        color: #667085;
        font-weight: 700;
    }
    .prediction-status.wrong {
        color: #dc3545;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def login_screen():
    st.header("Welcome to Predictor App for IPL 2025")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)


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
        return "{}"
    return data_frame.fillna("").to_json(
        orient="records", date_format="iso", date_unit="s"
    )


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


def get_booster_information(match_status, user_name):

    user_name = str(user_name).replace(" ", "").lower()
    match_id = match_status.get("MatchNumber")

    booster_data_found = False
    s3object = f"{user_name}/{get_booster_data_file(match_id)}"
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=s3object)
        booster_data_found = True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            booster_data_found = False
        else:
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


def get_individual_data_from_backend(match_id):

    ## Add headers
    user_name = str(st.session_state.user_name).replace(" ", "").lower()

    s3object = f"{user_name}/{user_name}_{match_id}.json"
    s3 = boto3.client("s3")
    try:
        data = s3.get_object(Bucket=BUCKET_NAME, Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        return contents.get("Selections")

    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            return False


def get_aggregate_transactional_data():
    s3 = boto3.client("s3")
    try:
        data = s3.get_object(Bucket=BUCKET_NAME, Key="aggregates/transactional.txt")
        return pd.DataFrame(json.loads(data["Body"].read().decode("utf-8")))
    except botocore.exceptions.ClientError:
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "..", "transactional.txt"
        )
        try:
            return pd.read_json(local_path)
        except ValueError:
            return pd.DataFrame()


def get_selected_match_label():
    selected_option = st.session_state.get("selected_option")
    if not selected_option:
        return None
    return selected_option.split(" (")[0]


def render_stat_cards(df):
    if df.empty:
        return
    columns = st.columns(2)
    team_a = list(df.columns)[1]
    team_b = list(df.columns)[2]

    def _as_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _winner_classes(home_value, away_value):
        if home_value == away_value:
            return "good", "good"
        return ("good", "bad") if away_value == "Lost" else ("bad", "good")

    def _metric_classes(stat_name, home_value, away_value):
        if stat_name == "Winner of the game":
            return _winner_classes(str(home_value), str(away_value))

        home_num = _as_float(home_value)
        away_num = _as_float(away_value)
        if home_num is None or away_num is None or home_num == away_num:
            return "good", "good"

        lower_is_better = stat_name in ["Total Wickets", "Total Dot Balls"]
        if lower_is_better:
            return ("good", "bad") if home_num < away_num else ("bad", "good")
        return ("good", "bad") if home_num > away_num else ("bad", "good")

    for idx, stat_row in df.iterrows():
        home_class, away_class = _metric_classes(
            stat_row["Stats"], stat_row.iloc[1], stat_row.iloc[2]
        )
        with columns[idx % 2]:
            st.markdown(
                f"""
                <div class="stat-compare-card">
                    <div class="title">{html.escape(str(stat_row["Stats"]))}</div>
                    <div class="value-row">
                        <div class="value-chip {home_class}">{html.escape(str(team_a))}: {html.escape(str(stat_row.iloc[1]))}</div>
                        <div class="value-chip {away_class}">{html.escape(str(team_b))}: {html.escape(str(stat_row.iloc[2]))}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_booster_strip(selected_booster_value):
    booster_items = [(5, "5x", "🔥🔥🔥🔥🔥"), (3, "3x", "🔥🔥🔥"), (2, "2x", "🔥🔥")]
    pills = []
    for value, label, icon in booster_items:
        css = (
            "booster-pill active" if selected_booster_value == value else "booster-pill"
        )
        pills.append(f'<span class="{css}">{icon} {label}</span>')
    st.markdown(
        f'<div class="booster-strip">{"".join(pills)}</div>', unsafe_allow_html=True
    )


def get_prediction_status(question_text, your_prediction, correct_prediction):
    question_lookup = {
        entry.get("questions"): {
            "q_key": entry.get("q_key"),
            "points": float(entry.get("points", 0)),
        }
        for entry in st.session_state.json_metadata.get("question_list", [])
    }
    question_meta = question_lookup.get(question_text, {})
    q_key = question_meta.get("q_key", "")
    base_points = question_meta.get("points", 0)
    results_published = st.session_state.get("current_match_status", {}).get(
        "ResultsPublished", False
    )
    your_value = "" if pd.isna(your_prediction) else str(your_prediction).strip()
    correct_value = (
        "" if pd.isna(correct_prediction) else str(correct_prediction).strip()
    )

    if not results_published and q_key in ["totalscore", "highest_over_score"]:
        return "unavailable", "Not Available"

    if correct_value in ["", "NOT_PUBLISHED", "Not Available"]:
        return "unavailable", "Not Available"

    if q_key in ["totalscore", "highest_over_score"]:
        try:
            your_score = float(your_value)
            correct_score = float(correct_value)
            if correct_score == 0:
                return (
                    ("correct", "Accurate")
                    if your_score == correct_score
                    else ("wrong", "Not Accurate")
                )

            closeness_ratio = max(
                0.0, 1 - (abs(correct_score - your_score) / abs(correct_score))
            )
            if (closeness_ratio * base_points) >= (0.8 * base_points):
                return "correct", "Accurate"
            if (closeness_ratio * base_points) >= (0.5 * base_points):
                return "partial", "Moderately Accurate"
            return "wrong", "Not Accurate"
        except (TypeError, ValueError):
            return "wrong", "Not Accurate"

    if correct_value == "Tie" and your_value != "":
        return "correct", "Correct"
    if your_value == correct_value:
        return "correct", "Correct"
    return "wrong", "Wrong"


def render_prediction_cards(df_player):
    question_lookup = {
        entry.get("questions"): entry.get("q_key")
        for entry in st.session_state.json_metadata.get("question_list", [])
    }
    results_published = st.session_state.get("current_match_status", {}).get(
        "ResultsPublished", False
    )
    for _, prediction_row in df_player.iterrows():
        status_class, status_label = get_prediction_status(
            prediction_row["Question"],
            prediction_row["Your Prediction"],
            prediction_row["Correct Prediction"],
        )
        q_key = question_lookup.get(prediction_row["Question"], "")
        correct_prediction_display = str(prediction_row["Correct Prediction"])
        if (
            correct_prediction_display in ["NOT_PUBLISHED", "", "nan"]
            or (not results_published and q_key in ["totalscore", "highest_over_score"])
        ):
            correct_prediction_display = "Not Available"
        st.markdown(
            f"""
            <div class="prediction-card {status_class}">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:0.8rem;">
                    <div style="font-weight:700;">{html.escape(str(prediction_row["Question"]))}</div>
                    <div>{html.escape(str(prediction_row["Points"]))} pts</div>
                </div>
                <div style="margin-top:0.35rem;color:var(--app-muted);">
                    Your pick: {html.escape(str(prediction_row["Your Prediction"]))} | Correct: {html.escape(correct_prediction_display)}
                </div>
                <div class="prediction-status {status_class}" style="margin-top:0.28rem;">{status_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def update_statistics():

    st.session_state.booster_value = 1

    if (
        st.session_state.selected_option == "Choose a match"
        or st.session_state.selected_option is None
    ):
        return 0
    selected_match_number = str(st.session_state.selected_option).split("-")[0].strip()

    match_status = {}
    for selected_entry in st.session_state.json_match:
        if selected_entry.get("MatchNumber") == int(selected_match_number):
            match_status = selected_entry
        else:
            continue

    _booster_1, _booster_2, _booster_3, contents_booster = get_booster_information(
        match_status, st.session_state.user_name
    )

    for booster in contents_booster.keys():
        if contents_booster.get(booster) == int(selected_match_number):
            booster_details = (
                "5x"
                if booster == "booster_1"
                else "3x"
                if booster == "booster_2"
                else "2x"
            )
            st.session_state.booster_value = int(booster_details.replace("x", ""))

    st.session_state.current_match_status = match_status

    if not match_status.get("ResultsPublished"):
        st.session_state.statistics_url = "Not Available"
        df = pd.DataFrame(
            {
                "Stats": ["Not Available"],
                f"{match_status.get('HomeTeam')}": ["Not Available"],
                f"{match_status.get('AwayTeam')}": ["Not Available"],
            }
        )
        st.session_state.df = df
        ## You Individual Prediction

        questions = []
        prediction = []
        correct = []
        point = []

        for question in st.session_state.json_metadata.get("question_list"):
            questions.append(question.get("questions"))
            correct_selection = match_status.get("PredictionResults").get(
                question.get("q_key")
            )
            correct.append(correct_selection)

            match_selection = get_individual_data_from_backend(
                match_status.get("MatchNumber")
            )
            user_selection = ""
            if match_selection:
                for q_key in match_selection:
                    if q_key.get("q_key") == question.get("q_key"):
                        user_selection = q_key.get("q_val")
                        break
                    else:
                        continue
            else:
                if question.get("q_key") in ["totalscore", "highest_over_score"]:
                    user_selection = 0
                else:
                    user_selection = ""
            prediction.append(str(user_selection))

            # Point Selection

            point.append("0")

        df_player = pd.DataFrame(
            {
                "Question": questions,
                "Your Prediction": prediction,
                "Correct Prediction": correct,
                "Points": point,
            }
        )
        st.session_state.df_player = df_player

    else:
        st.session_state.statistics_url = match_status.get("ResultsStats").get(
            "StatsLink"
        )
        # Get the Status By Team
        stats_list = []
        home_team = []
        away_team = []
        for question in st.session_state.json_metadata.get("question_list"):
            stats_list.append(question.get("stats_key"))
            home_team.append(
                match_status.get("ResultsStats").get(
                    f"HomeTeam_{question.get('q_key')}"
                )
            )
            away_team.append(
                match_status.get("ResultsStats").get(
                    f"AwayTeam_{question.get('q_key')}"
                )
            )

        df = pd.DataFrame(
            {
                "Stats": stats_list,
                f"{match_status.get('HomeTeam')}": home_team,
                f"{match_status.get('AwayTeam')}": away_team,
            }
        )
        st.session_state.df = df

        ## You Individual Prediction

        questions = []
        prediction = []
        correct = []
        point = []

        for question in st.session_state.json_metadata.get("question_list"):
            questions.append(question.get("questions"))
            correct_selection = match_status.get("PredictionResults").get(
                question.get("q_key")
            )
            correct.append(correct_selection)

            match_selection = get_individual_data_from_backend(
                match_status.get("MatchNumber")
            )
            user_selection = ""
            if match_selection:
                for q_key in match_selection:
                    if q_key.get("q_key") == question.get("q_key"):
                        user_selection = q_key.get("q_val")
                        break
                    else:
                        continue
            else:
                if question.get("q_key") in ["totalscore", "highest_over_score"]:
                    user_selection = 0
                else:
                    user_selection = ""
            prediction.append(str(user_selection))

            # Point Selection

            if question.get("q_key") in ["totalscore", "highest_over_score"]:
                correct_score = int(correct_selection)
                your_score = int(user_selection) if user_selection != "" else 0

                percentage_deviation = round(
                    (
                        (
                            abs(
                                100
                                - abs(
                                    ((correct_score - your_score) / (correct_score))
                                    * 100
                                )
                            )
                        )
                        / 100
                    )
                    * int(question.get("points")),
                    2,
                )
                point.append(str(percentage_deviation * st.session_state.booster_value))
            else:
                if correct_selection == "Tie" and user_selection != "":
                    point.append(
                        str(question.get("points") * st.session_state.booster_value)
                    )
                else:
                    if user_selection == correct_selection:
                        point.append(
                            str(question.get("points") * st.session_state.booster_value)
                        )
                    else:
                        point.append(str(0))

        df_player = pd.DataFrame(
            {
                "Question": questions,
                "Your Prediction": prediction,
                "Correct Prediction": correct,
                "Points": point,
            }
        )
        st.session_state.df_player = df_player


if getattr(st, "suspend", False):
    st.header("Due to Operations Sindoor !! Prediction game is suspended")
else:
    if socket.gethostname() == "MacBookPro.lan":
        st.session_state.user_name = "Gururaj Rao"
        st.session_state.next_matches = json.loads(get_next_match_from_json())
        if len(st.session_state.next_matches) != 0:
            st.session_state.current_match_dictionary = st.session_state.next_matches[0]
        else:
            st.session_state.current_match_dictionary = {}

        st.subheader("Choose a match to unlock analytics")
        match_number_current = st.session_state.current_match_dictionary.get(
            "MatchNumber", 0
        )
        selections = []
        for option_entry in st.session_state.json_match:
            if option_entry.get(
                "MatchCompletionStatus"
            ) == "Completed" or option_entry.get("MatchNumber") == (
                match_number_current - 1
            ):
                display_match_number = (
                    str(option_entry.get("MatchNumber"))
                    if option_entry.get("MatchNumber") > 9
                    else f"0{option_entry.get('MatchNumber')}"
                )
                if option_entry.get("MatchNumber") == (match_number_current - 1):
                    if option_entry.get("MatchCompletionStatus") == "Completed":
                        selections.append(
                            f"{display_match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} ({option_entry.get('MatchCompletionStatus')})"
                        )
                    else:
                        selections.append(
                            f"{display_match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} (In Progress)"
                        )
                else:
                    selections.append(
                        f"{display_match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} ({option_entry.get('MatchCompletionStatus')})"
                    )
        selections.sort(reverse=True)
        st.selectbox(
            "Pick The Game",
            options=selections,
            on_change=update_statistics,
            # index=None,
            # placeholder="Choose a match",
            key="selected_option",
            disabled=False,
        )
        update_statistics()

        with st.container():
            st.divider()
            st.subheader("Match Stat Cards")
            render_booster_strip(st.session_state.booster_value)
            if "statistics_url" in st.session_state:
                st.markdown(
                    f"Statistics Provided by [espncricinfo]({st.session_state.statistics_url})"
                )
            if "df" in st.session_state:
                render_stat_cards(st.session_state.df)

            st.divider()
            st.subheader("Prediction Results for the Match")
            if "df_player" in st.session_state:
                render_prediction_cards(st.session_state.df_player)

        # Render Statistics

        st.button("Log out", on_click=st.logout)
    else:
        if not st.user.is_logged_in or "name" not in st.user:
            login_screen()
        else:
            st.session_state.user_name = st.user.name
            st.session_state.next_matches = json.loads(get_next_match_from_json())
            if len(st.session_state.next_matches) != 0:
                st.session_state.current_match_dictionary = (
                    st.session_state.next_matches[0]
                )
            else:
                st.session_state.current_match_dictionary = {}

            st.subheader("Choose a match to unlock analytics")
            match_number_current = st.session_state.current_match_dictionary.get(
                "MatchNumber", 0
            )
            selections = []
            for match_entry in st.session_state.json_match:
                if match_entry.get(
                    "MatchCompletionStatus"
                ) == "Completed" or match_entry.get("MatchNumber") == (
                    match_number_current - 1
                ):
                    display_match_number = (
                        str(match_entry.get("MatchNumber"))
                        if match_entry.get("MatchNumber") > 9
                        else f"0{match_entry.get('MatchNumber')}"
                    )
                    if match_entry.get("MatchNumber") == (match_number_current - 1):
                        if match_entry.get("MatchCompletionStatus") == "Completed":
                            selections.append(
                                f"{display_match_number} - {match_entry.get('HomeTeam')} vs {match_entry.get('AwayTeam')} ({match_entry.get('MatchCompletionStatus')})"
                            )
                        else:
                            selections.append(
                                f"{display_match_number} - {match_entry.get('HomeTeam')} vs {match_entry.get('AwayTeam')} (In Progress)"
                            )
                    else:
                        selections.append(
                            f"{display_match_number} - {match_entry.get('HomeTeam')} vs {match_entry.get('AwayTeam')} ({match_entry.get('MatchCompletionStatus')})"
                        )
            selections.sort(reverse=True)
            st.selectbox(
                "Pick The Game",
                options=selections,
                on_change=update_statistics,
                # index=None,
                # placeholder="Choose a match",
                key="selected_option",
            )

            update_statistics()

            with st.container():
                st.divider()
                st.subheader("Match Stat Cards")
                render_booster_strip(st.session_state.booster_value)
                if "statistics_url" in st.session_state:
                    st.markdown(
                        f"Statistics Provided by [link]({st.session_state.statistics_url})"
                    )
                if "df" in st.session_state:
                    render_stat_cards(st.session_state.df)

                st.divider()
                st.subheader("Prediction Results for the Match")
                if "df_player" in st.session_state:
                    render_prediction_cards(st.session_state.df_player)
            st.button("Log out", on_click=st.logout)

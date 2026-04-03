import json
import os
import socket
import datetime as dt
import boto3
from datetime import datetime
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

st.set_page_config(
    page_title="Predictor Home Page",
    page_icon="https://brandlogos.net/wp-content/uploads/2021/12/indian_premier_league-brandlogo.net_.png",
)
Navbar()
apply_theme("", "")


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
            text-decoration: none;
            color: inherit;
        }
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


def get_booster_information():

    if len(st.session_state.next_matches) == 0:
        # st.subheader("No Matches to be played")
        return False, False, False, {}
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

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


def store_booster_information():

    if len(st.session_state.next_matches) == 0:
        # st.subheader("No Matches to be played")
        return False, False, False, {}
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        _booster_1, _booster_2, _booster_3, booster_data = get_booster_information()

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


def clear_booster_details():

    if len(st.session_state.next_matches) == 0:
        # st.subheader("No Matches to be played")
        return False, False, False, {}
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        _booster_1, _booster_2, _booster_3, booster_data = get_booster_information()

        for booster_keys in booster_data.keys():
            if booster_data.get(booster_keys) == match_id:
                booster_data[booster_keys] = 0
            else:
                continue

        s3object = f"{user_name}/match_booster.json"

        s3 = boto3.resource("s3")
        s3object = s3.Object(BUCKET_NAME, s3object)
        s3object.put(Body=(bytes(json.dumps(booster_data).encode("UTF-8"))))


def store_data_values():

    if len(st.session_state.next_matches) == 0:
        # st.subheader("No Matches to be played")
        pass
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")
        json_data = {
            "UserName": user_name,
            "MatchId": match_id,
            "MatchTime": match_details.get("DateUtc"),
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

        store_booster_information()


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


def body_rendering():
    ## Now lets add match details.

    if len(st.session_state.next_matches) == 0:
        # st.subheader("No Matches to be played")
        pass
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]
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
        # middle.image(
        #     "https://www.creativefabrica.com/wp-content/uploads/2021/11/09/Versus-Vs-Vector-Transparent-Background-Graphics-19913250-2-580x386.png"
        # )


def form_rendering():

    if len(st.session_state.next_matches) == 0:
        # st.subheader("No Matches to be played")
        pass
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        st.subheader("Select Booster for this match")
        booster_1, booster_2, booster_3 = st.columns(3, border=True)
        st.divider()

        booster_5x, booster_3x, booster_2x, booster_data = get_booster_information()

        booster_1.markdown("#### 5x Booster")

        booster_1.toggle(
            "5x 🔥🔥🔥🔥🔥",
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
        booster_2.markdown("#### 3x Booster")
        booster_2.toggle(
            "3x 🔥🔥🔥 ",
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
        booster_3.markdown("#### 2x Booster")
        booster_3.toggle(
            "2x 🔥🔥",
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

        with st.form("predictions", clear_on_submit=True, enter_to_submit=False):
            st.subheader("Select Predictions for this match")
            for question in st.session_state.json_metadata.get("question_list"):
                left_container, right_container = st.columns(2, border=False)
                left_container.markdown(
                    f"**{question.get('questions')}**\n\n{question.get('points')} points available"
                )
                if question.get("display_type") == "radio":
                    right_container.radio(
                        label="Select Below",
                        options=[
                            match_details.get("HomeTeam"),
                            match_details.get("AwayTeam"),
                        ],
                        key=question.get("q_key"),
                    )
                elif question.get("display_type") == "slider" and question.get(
                    "q_key"
                ) in ["totalscore"]:
                    right_container.slider(
                        label="Select Below",
                        key=question.get("q_key"),
                        min_value=1,
                        max_value=600,
                    )
                elif question.get("display_type") == "slider" and question.get(
                    "q_key"
                ) in ["highest_over_score"]:
                    right_container.slider(
                        label="Select Below",
                        key=question.get("q_key"),
                        min_value=1,
                        max_value=45,
                    )
                else:
                    continue
            st.form_submit_button("Submit Predictions", on_click=store_data_values)


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


def clear_selections():

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
            s3.delete_object(Bucket=BUCKET_NAME, Key=s3object)
            clear_booster_details()
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                return True
        return True


def display_details_of_the_prediction():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]
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
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                return True
        return True


if st.suspend == True:
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
            body_rendering()
            ## Add Questions
            check_match_date_selected = check_match_date_selected()
            if not check_match_date_selected:
                form_rendering()
            else:
                st.subheader("Your selections are locked for today")
                display_details_of_the_prediction()

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
            body_rendering()
            check_match_date_selected = check_match_date_selected()
            if not check_match_date_selected:
                form_rendering()
            else:
                st.subheader("Your selections are locked for today")
                display_details_of_the_prediction()
            ## Add Questions

            st.button("Log out", on_click=st.logout)

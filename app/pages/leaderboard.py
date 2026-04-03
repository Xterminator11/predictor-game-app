import streamlit as st
import json
import boto3
import os
import pandas as pd
from modules.navigator import Navbar
from modules.ui import (
    apply_theme,
    render_info_card,
    render_list_card,
    render_rank_card,
    render_page_header,
)
import socket
import botocore

from modules.util_app import get_bucket_name, get_match_details_json

BUCKET_NAME = get_bucket_name()

st.set_page_config(
    page_title="Leader Board",
    page_icon="https://brandlogos.net/wp-content/uploads/2021/12/indian_premier_league-brandlogo.net_.png",
)

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
    "Leaderboard",
    "See who is leading the tournament, how boosters changed the race, and how each player has performed match by match.",
    "Tournament Race",
)


def login_screen():
    st.header("Welcome to Predictor App for IPL 2025")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)


def get_aggregate_data():

    ## Add headers
    user_name = str(st.session_state.user_name).replace(" ", "").lower()

    s3 = boto3.client("s3")
    try:
        s3object = "aggregates/leaderboard.txt"
        data = s3.get_object(Bucket=BUCKET_NAME, Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        st.session_state.df_leaderboard = pd.DataFrame(contents)

        s3object = "aggregates/transactional.txt"
        data = s3.get_object(Bucket=BUCKET_NAME, Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        df = pd.DataFrame(contents)
        st.session_state.df_all = df
        st.session_state.df_individual = df[df["UserName"] == user_name].reset_index(
            drop=True
        )

    except botocore.exceptions.ClientError as e:
        try:
            st.session_state.df_leaderboard = pd.read_json(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "..", "leaderboard.txt"
                )
            )
            st.session_state.df_all = pd.read_json(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "..",
                    "transactional.txt",
                )
            )
            st.session_state.df_individual = st.session_state.df_all[
                st.session_state.df_all["UserName"] == user_name
            ].reset_index(drop=True)
        except ValueError:
            return False
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            return False


def get_user_name():
    if "df_all" not in st.session_state:
        return []
    else:
        df_user_name_list = (
            st.session_state.df_all.sort_values(by="UserName")["UserName"]
            .unique()
            .tolist()
        )
        return df_user_name_list


def get_user_data():

    if (
        st.session_state.user_select == "Select a User"
        or st.session_state.user_select is None
    ):
        return 0

    st.session_state.df_selected = st.session_state.df_all[
        st.session_state.df_all["UserName"] == st.session_state.user_select
    ].reset_index(drop=True)


def format_score(value):
    return f"{float(value):.2f}"


def format_booster_display(booster_indicator):
    indicator = str(booster_indicator or "").strip()
    booster_map = {
        "5x": "🔥🔥🔥🔥🔥 5x",
        "3x": "🔥🔥🔥 3x",
        "2x": "🔥🔥 2x",
    }
    return booster_map.get(indicator, "No booster")


def render_top_three(df_leaderboard):
    ordered = df_leaderboard.sort_values(
        by="AggregatePoints", ascending=False
    ).reset_index(drop=True)
    trophies = [("1st Place", "🥇"), ("2nd Place", "🥈"), ("3rd Place", "🥉")]
    columns = st.columns(3)
    for idx, column in enumerate(columns):
        with column:
            if idx < len(ordered):
                row = ordered.iloc[idx]
                render_rank_card(
                    trophies[idx][0],
                    trophies[idx][1],
                    str(row["UserName"]),
                    format_score(row["AggregatePoints"]),
                    "Tournament aggregate points",
                )
            else:
                render_info_card(
                    "Open Podium", "No player data available for this rank yet."
                )


def render_ranked_list(df_leaderboard):
    ordered = df_leaderboard.sort_values(
        by="AggregatePoints", ascending=False
    ).reset_index(drop=True)
    for idx, row in ordered.iloc[3:].iterrows():
        render_list_card(
            f"#{idx + 1} {row['UserName']}",
            format_score(row["AggregatePoints"]),
            "Total tournament points",
        )


def render_user_match_cards(df, title):
    st.subheader(title)
    if df.empty:
        st.info("No records available yet.")
        return
    sorted_df = df.sort_values(by="AggregatePoints", ascending=False).reset_index(
        drop=True
    )
    for _, row in sorted_df.iterrows():
        booster = format_booster_display(row.get("BoosterIndicator", ""))
        render_list_card(
            str(row["MatchNumber"]),
            format_score(row["AggregatePoints"]),
            f"Booster: {booster}",
        )


def render_leaderboard_view():
    st.subheader("Podium")
    if (
        "df_leaderboard" in st.session_state
        and not st.session_state.df_leaderboard.empty
    ):
        render_top_three(st.session_state.df_leaderboard)
        st.markdown("### Full Standings")
        render_ranked_list(st.session_state.df_leaderboard)
    else:
        st.info("Leaderboard data is not available yet.")

    insight_left, insight_middle, insight_right = st.columns(3)
    if "df_all" in st.session_state and not st.session_state.df_all.empty:
        df_all = st.session_state.df_all.copy()
        insight_left.metric("Matches Tracked", df_all["MatchNumber"].nunique())
        insight_middle.metric(
            "Total Boosters Used",
            int((df_all["BoosterIndicator"].fillna("") != "").sum()),
        )
        insight_right.metric(
            "Highest Single Match",
            format_score(df_all["AggregatePoints"].max()),
        )

    st.divider()
    if "df_individual" in st.session_state:
        render_user_match_cards(st.session_state.df_individual, "Your Match Cards")

    st.divider()
    st.subheader("Compare Another User")
    st.selectbox(
        "Select User",
        options=get_user_name(),
        key="user_select",
        on_change=get_user_data,
        index=0,
        placeholder="Select a User",
    )
    get_user_data()
    if "df_selected" in st.session_state:
        render_user_match_cards(
            st.session_state.df_selected, "Selected User Match Cards"
        )


if getattr(st, "suspend", False):
    st.header("Due to Operations Sindoor !! Prediction game is suspended")
else:
    if socket.gethostname() == "MacBookPro.lan":
        st.session_state.user_name = "Gururaj Rao"
        get_aggregate_data()
        render_leaderboard_view()

        st.button("Log out", on_click=st.logout)
    else:
        if not st.user.is_logged_in or "name" not in st.user:
            login_screen()
        else:
            st.session_state.user_name = st.user.name
        get_aggregate_data()
        render_leaderboard_view()

        st.button("Log out", on_click=st.logout)

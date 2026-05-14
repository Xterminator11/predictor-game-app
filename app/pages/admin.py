import streamlit as st
import json
import os
import pandas as pd
from modules.navigator import Navbar
from modules.ui import apply_theme, render_info_card, render_page_header
import socket
import datetime as dt

from modules.util_app import (
    get_bucket_name,
    get_match_details_json,
    put_match_details_json,
)

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
    "Admin Control Center",
    "Manage match results, publish official stats, and keep the scoring engine synchronized without changing the admin workflow.",
    "Admin Operations",
)


def refresh_match_details():
    st.session_state.json_match = json.loads(get_match_details_json(data_type="json"))


def login_screen():
    st.header("Welcome to Predictor App for IPL 2026")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)


def update_results(input_metrics):
    if input_metrics == "totalscore":
        return (
            st.session_state.HomeTeam_totalscore + st.session_state.AwayTeam_totalscore
        )
    elif input_metrics == "highest_over_score":
        return max(
            st.session_state.HomeTeam_highest_over_score,
            st.session_state.AwayTeam_highest_over_score,
        )
    elif input_metrics == "winner":
        return (
            st.session_state.home_team
            if st.session_state.HomeTeam_winner == "Won"
            else st.session_state.away_team
        )
    elif input_metrics == "wickets":
        if st.session_state.HomeTeam_wickets == st.session_state.AwayTeam_wickets:
            return "Tie"
        else:
            return (
                st.session_state.home_team
                if st.session_state.AwayTeam_wickets > st.session_state.HomeTeam_wickets
                else st.session_state.away_team
            )
    elif input_metrics == "dotballs":
        if st.session_state.HomeTeam_dotballs == st.session_state.AwayTeam_dotballs:
            return "Tie"
        return (
            st.session_state.home_team
            if st.session_state.HomeTeam_dotballs < st.session_state.AwayTeam_dotballs
            else st.session_state.away_team
        )
    else:
        if st.session_state.get(f"HomeTeam_{input_metrics}") == st.session_state.get(
            f"AwayTeam_{input_metrics}"
        ):
            return "Tie"
        else:
            return (
                st.session_state.home_team
                if st.session_state.get(f"HomeTeam_{input_metrics}")
                > st.session_state.get(f"AwayTeam_{input_metrics}")
                else st.session_state.away_team
            )


def store_match_details():
    st.text("Match Submitted")

    match_details = []
    # update_match_label()
    st.session_state.match_number_selected = int(
        st.session_state.selected_option.split("-")[0].strip()
    )

    print(f"Current match number selected: {st.session_state.match_number_selected}")
    for result_entry in st.session_state.json_match:
        print(f"Current match number in loop: {result_entry.get('MatchNumber')}")
        if result_entry.get("MatchNumber") == st.session_state.match_number_selected:
            result_entry["PredictionResults"] = {
                "winner": update_results("winner"),
                "fours": update_results("fours"),
                "sixes": update_results("sixes"),
                "wickets": update_results("wickets"),
                "powerplay": update_results("powerplay"),
                "dotballs": update_results("dotballs"),
                "totalscore": str(update_results("totalscore")),
                "highest_over_score": str(update_results("highest_over_score")),
            }
            result_entry["ResultsStats"] = {
                "HomeTeam_totalscore": str(st.session_state.HomeTeam_totalscore),
                "HomeTeam_wickets": str(st.session_state.HomeTeam_wickets),
                "AwayTeam_totalscore": str(st.session_state.AwayTeam_totalscore),
                "AwayTeam_wickets": str(st.session_state.AwayTeam_wickets),
                "AwayTeam_fours": str(st.session_state.AwayTeam_fours),
                "AwayTeam_sixes": str(st.session_state.AwayTeam_sixes),
                "HomeTeam_fours": str(st.session_state.HomeTeam_fours),
                "HomeTeam_sixes": str(st.session_state.HomeTeam_sixes),
                "HomeTeam_powerplay": str(st.session_state.HomeTeam_powerplay),
                "AwayTeam_powerplay": str(st.session_state.AwayTeam_powerplay),
                "HomeTeam_dotballs": str(st.session_state.HomeTeam_dotballs),
                "AwayTeam_dotballs": str(st.session_state.AwayTeam_dotballs),
                "HomeTeam_highest_over_score": str(
                    st.session_state.HomeTeam_highest_over_score
                ),
                "AwayTeam_highest_over_score": str(
                    st.session_state.AwayTeam_highest_over_score
                ),
                "HomeTeam_winner": str(st.session_state.HomeTeam_winner),
                "AwayTeam_winner": str(st.session_state.AwayTeam_winner),
                "StatsLink": str(st.session_state.StatsLink),
            }
            result_entry["MatchCompletionStatus"] = "Completed"
            result_entry["ResultsPublished"] = True

            match_details.append(result_entry)
        else:
            match_details.append(result_entry)

    put_match_details_json(match_details)
    st.session_state.json_match = json.loads(get_match_details_json(data_type="json"))

    # # Run Aggregation Logic Here
    # try:
    #     run_aggregate_cycle()
    #     st.success(
    #         "Match details updated and aggregation cycle completed successfully!"
    #     )
    # except Exception as e:
    #     st.error(f"An error occurred while running the aggregation cycle: {str(e)}")


def update_match_label():
    if "selected_option" in st.session_state:

        def _int_or_zero(value):
            if value in (None, "", "NOT_PUBLISHED"):
                return 0
            return int(value)

        st.session_state.home_team = (
            st.session_state.selected_option.split("-")[1]
            .split("(")[0]
            .split("vs")[0]
            .strip()
        )
        st.session_state.away_team = (
            st.session_state.selected_option.split("-")[1]
            .split("(")[0]
            .split("vs")[1]
            .strip()
        )

        st.session_state.match_number_selected = int(
            st.session_state.selected_option.split("-")[0].strip()
        )

        print(f"Selected Match Number: {st.session_state.match_number_selected}")
        # Update Values

        for result_entry in st.session_state.json_match:
            if (
                result_entry.get("MatchNumber")
                == st.session_state.match_number_selected
            ):
                results_stats = result_entry.get("ResultsStats", {})
                st.session_state["HomeTeam_totalscore"] = _int_or_zero(
                    results_stats.get("HomeTeam_totalscore")
                )
                st.session_state.HomeTeam_wickets = _int_or_zero(
                    results_stats.get("HomeTeam_wickets")
                )
                st.session_state.AwayTeam_totalscore = _int_or_zero(
                    results_stats.get("AwayTeam_totalscore")
                )
                st.session_state.AwayTeam_wickets = _int_or_zero(
                    results_stats.get("AwayTeam_wickets")
                )
                st.session_state.AwayTeam_fours = _int_or_zero(
                    results_stats.get("AwayTeam_fours")
                )
                st.session_state.AwayTeam_sixes = _int_or_zero(
                    results_stats.get("AwayTeam_sixes")
                )
                st.session_state.HomeTeam_fours = _int_or_zero(
                    results_stats.get("HomeTeam_fours")
                )
                st.session_state.HomeTeam_sixes = _int_or_zero(
                    results_stats.get("HomeTeam_sixes")
                )
                st.session_state.HomeTeam_powerplay = _int_or_zero(
                    results_stats.get("HomeTeam_powerplay")
                )
                st.session_state.AwayTeam_powerplay = _int_or_zero(
                    results_stats.get("AwayTeam_powerplay")
                )
                st.session_state.HomeTeam_dotballs = _int_or_zero(
                    results_stats.get("HomeTeam_dotballs")
                )
                st.session_state.AwayTeam_dotballs = _int_or_zero(
                    results_stats.get("AwayTeam_dotballs")
                )
                st.session_state.HomeTeam_highest_over_score = _int_or_zero(
                    results_stats.get("HomeTeam_highest_over_score")
                )
                st.session_state.AwayTeam_highest_over_score = _int_or_zero(
                    results_stats.get("AwayTeam_highest_over_score")
                )
                st.session_state.HomeTeam_winner = (
                    results_stats.get("HomeTeam_winner")
                    if results_stats.get("HomeTeam_winner") != "NOT_PUBLISHED"
                    else "Won"
                )
                st.session_state.AwayTeam_winner = (
                    results_stats.get("AwayTeam_winner")
                    if results_stats.get("AwayTeam_winner") != "NOT_PUBLISHED"
                    else "Won"
                )
                st.session_state.StatsLink = (
                    results_stats.get("StatsLink")
                    if results_stats.get("StatsLink") != "NOT_PUBLISHED"
                    else "NOT_PUBLISHED"
                )
                break
            else:
                continue


def cleanup_previous_instance():
    for key in [
        "HomeTeam_totalscore",
        "HomeTeam_wickets",
        "AwayTeam_totalscore",
        "AwayTeam_wickets",
        "AwayTeam_fours",
        "AwayTeam_sixes",
        "HomeTeam_fours",
        "HomeTeam_sixes",
        "HomeTeam_powerplay",
        "AwayTeam_powerplay",
        "HomeTeam_dotballs",
        "AwayTeam_dotballs",
        "HomeTeam_highest_over_score",
        "AwayTeam_highest_over_score",
        "HomeTeam_winner",
        "AwayTeam_winner",
        "StatsLink",
    ]:
        if key in st.session_state:
            st.session_state.pop(key)
        else:
            continue


def create_input_form_match_details():
    # Do not clear values here. `update_match_label` populates session_state
    # when a match is selected, and clearing at render time wipes those values.
    render_info_card(
        "Admin Input",
        "Update the official match results carefully. Submitting this data changes published stats and downstream scoring.",
    )
    home_team, away_team = st.columns(2, gap="medium")
    st.text_input(label="StatsLink", key="StatsLink")
    st.button(label="Submit", on_click=store_match_details)
    with home_team:
        st.number_input(
            label=f"{st.session_state.home_team} Score",
            key="HomeTeam_totalscore",
            format="%u",
            min_value=0,
            max_value=300,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Wickets",
            key="HomeTeam_wickets",
            format="%u",
            min_value=0,
            max_value=10,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Fours",
            key="HomeTeam_fours",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Sixes",
            key="HomeTeam_sixes",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Powerplay",
            key="HomeTeam_powerplay",
            format="%u",
            min_value=0,
            max_value=150,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Dot Balls",
            key="HomeTeam_dotballs",
            format="%u",
            min_value=0,
            max_value=120,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Highest Over Score",
            key="HomeTeam_highest_over_score",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.selectbox(
            label=f"{st.session_state.home_team} Result",
            key="HomeTeam_winner",
            options=["Won", "Lost"],
        )
    with away_team:
        st.number_input(
            label=f"{st.session_state.away_team} Score",
            key="AwayTeam_totalscore",
            format="%u",
            min_value=0,
            max_value=300,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Wickets",
            key="AwayTeam_wickets",
            format="%u",
            min_value=0,
            max_value=10,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Fours",
            key="AwayTeam_fours",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Sixes",
            key="AwayTeam_sixes",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Powerplay",
            key="AwayTeam_powerplay",
            format="%u",
            min_value=0,
            max_value=150,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Dot Balls",
            key="AwayTeam_dotballs",
            format="%u",
            min_value=0,
            max_value=120,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Highest Over Score",
            key="AwayTeam_highest_over_score",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.selectbox(
            label=f"{st.session_state.away_team} Result",
            key="AwayTeam_winner",
            options=["Won", "Lost"],
        )


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


if socket.gethostname() == "Gururajs-MacBook-Pro.local":
    st.session_state.user_name = "Gururaj Rao"
    render_page_header(
        "Admin Page",
        "Select a match, update the official result fields, and publish the statistics used by the prediction engine.",
        "Restricted Access",
    )
    st.session_state.next_matches = json.loads(get_next_match_from_json())
    if len(st.session_state.next_matches) != 0:
        st.session_state.current_match_dictionary = st.session_state.next_matches[0]
    else:
        st.session_state.current_match_dictionary = {}

    if "home_team" not in st.session_state:
        st.session_state.home_team = "HomeTeam"
    if "away_team" not in st.session_state:
        st.session_state.away_team = "AwayTeam"
    if "match_number_selected" not in st.session_state:
        st.session_state.match_number_selected = 0

    if st.session_state.user_name == "Gururaj Rao":
        with st.container():
            st.subheader("Select team and update stats")
            selections = []
            for option_entry in st.session_state.json_match:
                if option_entry.get("MatchCompletionStatus") == "Completed" or (
                    option_entry.get("MatchNumber")
                    == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 1
                    )
                    or option_entry.get("MatchNumber")
                    == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 2
                    )
                    or option_entry.get("MatchNumber")
                    == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 3
                    )
                    or option_entry.get("MatchNumber")
                    == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 4
                    )
                    or option_entry.get("MatchNumber")
                    == (st.session_state.current_match_dictionary.get("MatchNumber"))
                ):
                    match_number = (
                        str(option_entry.get("MatchNumber"))
                        if option_entry.get("MatchNumber") > 9
                        else f"0{option_entry.get('MatchNumber')}"
                    )
                    if (
                        option_entry.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 1
                        )
                        or option_entry.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 2
                        )
                        or option_entry.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                        )
                    ):
                        if option_entry.get("MatchCompletionStatus") == "Completed":
                            selections.append(
                                f"{match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} ({option_entry.get('MatchCompletionStatus')})"
                            )
                        else:
                            selections.append(
                                f"{match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} (In Progress)"
                            )
                    else:
                        selections.append(
                            f"{match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} ({option_entry.get('MatchCompletionStatus')})"
                        )
            selections.sort(reverse=True)
            # create_input_form_match_details()
            st.selectbox(
                "Pick The Game",
                options=selections,
                on_change=update_match_label,
                # index=None,
                placeholder="Choose a match",
                key="selected_option",
                disabled=False,
            )
        with st.container():
            create_input_form_match_details()
        st.button("Log out", on_click=st.logout)
    else:
        st.error("You are not authorized to access this page", icon="‼️")
        # st.button("Log out", on_click=st.logout)
else:
    if not st.user.is_logged_in or "name" not in st.user:
        login_screen()
    else:
        st.session_state.user_name = st.user.name
        render_page_header(
            "Admin Page",
            "Select a match, update the official result fields, and publish the statistics used by the prediction engine.",
            "Restricted Access",
        )
        st.session_state.next_matches = json.loads(get_next_match_from_json())
        if len(st.session_state.next_matches) != 0:
            st.session_state.current_match_dictionary = st.session_state.next_matches[0]
        else:
            st.session_state.current_match_dictionary = {}

        if "home_team" not in st.session_state:
            st.session_state.home_team = "HomeTeam"
        if "away_team" not in st.session_state:
            st.session_state.away_team = "AwayTeam"
        if "match_number_selected" not in st.session_state:
            st.session_state.match_number_selected = 1

        if st.session_state.user_name == "Gururaj Rao":
            with st.container():
                st.subheader("Select team and update stats")
                selections = []
                for option_entry in st.session_state.json_match:
                    if option_entry.get("MatchCompletionStatus") == "Completed" or (
                        option_entry.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 1
                        )
                        or option_entry.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 2
                        )
                        or option_entry.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 3
                        )
                        or option_entry.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 4
                        )
                    ):
                        match_number = (
                            str(option_entry.get("MatchNumber"))
                            if option_entry.get("MatchNumber") > 9
                            else f"0{option_entry.get('MatchNumber')}"
                        )
                        if (
                            option_entry.get("MatchNumber")
                            == (
                                st.session_state.current_match_dictionary.get(
                                    "MatchNumber"
                                )
                                - 1
                            )
                            or option_entry.get("MatchNumber")
                            == (
                                st.session_state.current_match_dictionary.get(
                                    "MatchNumber"
                                )
                                - 2
                            )
                            or option_entry.get("MatchNumber")
                            == (
                                st.session_state.current_match_dictionary.get(
                                    "MatchNumber"
                                )
                            )
                        ):
                            if option_entry.get("MatchCompletionStatus") == "Completed":
                                selections.append(
                                    f"{match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} ({option_entry.get('MatchCompletionStatus')})"
                                )
                            else:
                                selections.append(
                                    f"{match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} (In Progress)"
                                )
                        else:
                            selections.append(
                                f"{match_number} - {option_entry.get('HomeTeam')} vs {option_entry.get('AwayTeam')} ({option_entry.get('MatchCompletionStatus')})"
                            )
                selections.sort(reverse=True)
                st.selectbox(
                    "Pick The Game",
                    options=selections,
                    on_change=update_match_label,
                    # index=None,
                    placeholder="Choose a match",
                    key="selected_option",
                    disabled=False,
                )

                create_input_form_match_details()
            st.button("Log out", on_click=st.logout)
        else:
            st.error("You are not authorized to access this page", icon="‼️")

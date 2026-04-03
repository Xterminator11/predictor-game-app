import json
import os

import pandas as pd
import streamlit as st

from modules.navigator import Navbar
from modules.ui import apply_theme, render_info_card


st.set_page_config(
    page_title="Help and Rules",
    page_icon="https://brandlogos.net/wp-content/uploads/2021/12/indian_premier_league-brandlogo.net_.png",
)

Navbar()
apply_theme("", "")
st.title("Help and Game Rules")
st.caption(
    "Everything you need in one place: navigation, scoring, boosters, and match-day strategy."
)

metadata = json.loads(
    open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.json"),
        "r",
        encoding="utf-8",
    ).read()
)

question_rules = {
    "winner": "Full 5 points if your selected team wins.",
    "fours": "Full 5 points if your selected team hits more fours.",
    "sixes": "Full 5 points if your selected team hits more sixes.",
    "wickets": "Full 5 points if your selected team takes more wickets.",
    "powerplay": "Full 5 points if your selected team scores more runs in the powerplay.",
    "dotballs": "Full 5 points if your selected team has the lower dot-ball percentage.",
    "totalscore": "Up to 10 points based on how close your total-score prediction is to the actual result.",
    "highest_over_score": "Up to 10 points based on how close your over-score prediction is to the actual result.",
}

phase_rows = [
    {
        "Phase": "Phase 1",
        "Match Range": "1 - 20",
        "Boosters Available": "1 x 5x, 1 x 3x, 1 x 2x",
        "Total Boosters": 3,
    },
    {
        "Phase": "Phase 2",
        "Match Range": "21 - 40",
        "Boosters Available": "1 x 5x, 1 x 3x, 1 x 2x",
        "Total Boosters": 3,
    },
    {
        "Phase": "Phase 3",
        "Match Range": "41 - 60",
        "Boosters Available": "1 x 5x, 1 x 3x, 1 x 2x",
        "Total Boosters": 3,
    },
    {
        "Phase": "Phase 4",
        "Match Range": "61 - 70",
        "Boosters Available": "1 x 5x, 1 x 3x, 1 x 2x",
        "Total Boosters": 3,
    },
    {
        "Phase": "Phase 5",
        "Match Range": "71 - 74",
        "Boosters Available": "1 x 5x, 1 x 3x, 1 x 2x",
        "Total Boosters": 3,
    },
]

question_rows = []
for question in metadata.get("question_list", []):
    question_rows.append(
        {
            "Question": question.get("questions"),
            "Type": question.get("display_type", "").title(),
            "Base Points": question.get("points"),
            "Scoring Rule": question_rules.get(
                question.get("q_key"), "Standard scoring applies."
            ),
        }
    )

base_points = sum(
    question.get("points", 0) for question in metadata.get("question_list", [])
)
total_boosters = sum(phase.get("Total Boosters", 0) for phase in phase_rows)

perfect_five_x = base_points * 5
perfect_three_x = base_points * 3
perfect_two_x = base_points * 2

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Questions Per Match", len(metadata.get("question_list", [])))
metric_2.metric("Base Points Per Match", base_points)
metric_3.metric("Total Boosters In Tournament", total_boosters)

st.divider()

st.header("1. How to Navigate the App")
st.markdown(
    """
    <style>
    .nav-equal-card .app-card {
        min-height: 196px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
nav_left, nav_middle, nav_right = st.columns(3)
with nav_left:
    st.markdown('<div class="nav-equal-card">', unsafe_allow_html=True)
    render_info_card(
        "Predictor Home Page",
        "Review the next match, choose a booster, answer all questions, and submit predictions before the match locks.",
    )
    st.markdown("</div>", unsafe_allow_html=True)
with nav_middle:
    st.markdown('<div class="nav-equal-card">', unsafe_allow_html=True)
    render_info_card(
        "Statistics and Leader Board",
        "Statistics shows your prediction breakdown. Leader Board tracks total scores, rank movement, and player comparisons.",
    )
    st.markdown("</div>", unsafe_allow_html=True)
with nav_right:
    st.markdown('<div class="nav-equal-card">', unsafe_allow_html=True)
    render_info_card(
        "Help and Admin",
        "Help explains the rules. Admin is reserved for authorized result and aggregation updates.",
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.info(
    "Use the left sidebar as your primary navigation. The normal player flow is Home Page, then Statistics, then Leader Board."
)

st.header("1.1 How to Play the Game")
st.markdown(
    """
1. Go to Predictor Home Page.
2. Review the upcoming match details shown at the top of the page.
3. Choose one booster for the match, or skip boosters if you want to save them.
4. Answer all prediction questions for that match.
5. Submit your selections before the match locks.
6. After results are published, check Statistics to see your score and Leader Board to see your overall position.
"""
)

st.info(
    "Only one booster can be selected for a match. The app disables the other booster options as soon as you choose one."
)

st.divider()

st.header("2. Point System Rules")
st.dataframe(
    pd.DataFrame(question_rows),
    use_container_width=True,
    hide_index=True,
)

st.success(
    f"If you answer every question correctly without using a booster, the base score for one match is {base_points} points."
)

st.markdown(
    """
Additional scoring notes:

- Radio questions give full points when your chosen team matches the published result.
- Slider questions are scored by closeness, so better estimates earn more points.
- After the base score is calculated, any selected booster multiplies the points for that match.
- On team-vs-team questions, if the published result is marked as a tie, the current scoring logic grants full points to any submitted selection for that question.
"""
)

st.subheader("Scoring Examples")
example_left, example_right = st.columns(2)
with example_left:
    render_info_card(
        "Example 1: Perfect Match With Booster",
        f"A perfect match earns {base_points} base points. That becomes {perfect_five_x} with 5x, {perfect_three_x} with 3x, and {perfect_two_x} with 2x.",
    )
with example_right:
    render_info_card(
        "Example 2: Slider Question Logic",
        "If the actual total score is 340 and you predict 320, you still earn partial points. Closer slider predictions score higher, and exact predictions get the full 10.",
    )

st.divider()

st.header("3. How the Booster System Works")
st.markdown(
    """
1. Every phase gives you three boosters: one 5x booster, one 3x booster, and one 2x booster.
2. A booster multiplies the points you earn for that match.
3. You can use at most one booster on a single match.
4. Once a specific booster is used in a phase, it cannot be reused in that same phase.
5. If you do not want to risk a multiplier on a match, leave all booster toggles off and play with normal scoring.
"""
)

booster_left, booster_middle, booster_right = st.columns(3)
booster_left.metric("5x Booster", "1 per phase")
booster_middle.metric("3x Booster", "1 per phase")
booster_right.metric("2x Booster", "1 per phase")

st.warning(
    "Boosters are tracked separately by phase. A booster used in one phase does not reduce your boosters in the next phase."
)

st.subheader("Booster Strategy Examples")
strategy_left, strategy_right = st.columns(2)
with strategy_left:
    render_info_card(
        "Safe Approach",
        "Save the 5x booster for matches where you are highly confident. Use the 2x booster in uncertain games where you still want some upside.",
    )
with strategy_right:
    render_info_card(
        "Phase Management",
        "Each phase resets your available boosters. If a phase is nearly over and you still have boosters left, use them before the reset.",
    )

st.divider()

st.header("4. Boosters Available in Each Phase")
st.dataframe(
    pd.DataFrame(phase_rows),
    use_container_width=True,
    hide_index=True,
)

st.markdown(
    f"Across the full tournament, the app currently supports {total_boosters} boosters in total: five 5x boosters, five 3x boosters, and five 2x boosters."
)

if st.button("🔥 Go to Predictor Home Page", type="primary", key="go_home_page"):
    st.switch_page("main.py")

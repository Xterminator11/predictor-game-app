import streamlit as st

from modules.ui import ensure_theme_state


def Navbar():
    # st.set_option("client.showSidebarNavigation", False)
    with st.sidebar:
        ensure_theme_state()
        st.markdown("## Predictor 2026")
        st.caption("IPL prediction experience")
        st.divider()
        st.page_link("main.py", label="Predictor Home Page", icon="🔥")
        # Ensure clicking Home clears stale match query param from URL
        st.components.v1.html(
            """<script>
            const links = window.parent.document.querySelectorAll('[data-testid="stPageLink-NavLink"]');
            if (links.length > 0) {
                links[0].addEventListener('click', function() {
                    window.parent.history.replaceState({}, '', window.parent.location.pathname);
                });
            }
            </script>""",
            height=0,
        )
        st.page_link("pages/stats.py", label="Statistics", icon="🛡️")
        st.page_link("pages/leaderboard.py", label="Leader Board", icon="🐐")
        st.page_link("pages/admin.py", label="Admin Page", icon="👨‍🏫")
        st.page_link("pages/help.py", label="Help", icon="❓")

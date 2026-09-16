import streamlit as st

st.set_page_config(
    page_title="Wycena tortów",
    page_icon="🎂",
    layout="wide",
)

navigation = st.navigation(
    [
        st.Page(
            "pages/01_Skladniki.py",
            title="Składniki",
            icon="🧺",
            default=True,
        ),
        st.Page(
            "pages/02_Przepisy.py",
            title="Przepisy",
            icon="📖",
        ),

        st.Page(
            "pages/04_Wycena.py",
            title="Wycena",
            icon="💰",
        ),
    ]
)

navigation.run()
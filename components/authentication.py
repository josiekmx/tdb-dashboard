import streamlit as st

# checks whether user is password aunthenticated,
# else brings them to login page
def check_password():
    # if user is already authenticated, skip login page
    if st.session_state.get("authenticated", False):
        return True
    
    # else login page is displayed
    st.title("The Daily Blooms Dashboard")
    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")

    return False
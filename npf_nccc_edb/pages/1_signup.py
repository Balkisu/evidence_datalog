import psycopg2
import streamlit as st

# Create a SessionState class for session management
class SessionState:
    def __init__(self, username=None, login_successful=False, is_superuser=False):
        self.username = username
        self.login_successful = login_successful
        self.is_superuser = is_superuser

# Initialize session state
def init_session_state():
    session_state = SessionState()
    return session_state

# Retrieve or create session state
session_state = st.session_state.get('session_state', init_session_state())

st.title("Sign Up")

st.markdown(
    """
    <style>
    .title {
        text-align: center;
        font-size: 32px;
        margin-bottom: 24px;
    }
    .sign-in {
        text-align: center;
        margin-bottom: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<h1 class="title">Create An Account</h1>', unsafe_allow_html=True)

# Retrieve PostgreSQL connection details from secrets
host = st.secrets["postgres"]["host"]
port = st.secrets["postgres"]["port"]
dbname = st.secrets["postgres"]["dbname"]
user = st.secrets["postgres"]["user"]
password = st.secrets["postgres"]["password"]

# Establish the connection
conn = psycopg2.connect(
    host=host,
    port=port,
    dbname=dbname,
    user=user,
    password=password
)

# Create a cursor
cursor = conn.cursor()

# Input fields
username = st.text_input("Username")
first_name = st.text_input("First Name")
last_name = st.text_input("Last Name")
password = st.text_input("Password", type="password")
is_superuser = st.checkbox("Is Superuser")

# Sign-up button
st.markdown(
    """
    <style>
    .button {
        display: block;
        width: 100%;
        padding: 12px;
        margin-top: 24px;
        text-align: center;
        font-size: 16px;
        color: #ffffff;
        background-color: #3366cc;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .button:hover {
        background-color: #2456a6;
    }
    .sign-in-link {
        text-align: center;
        margin-top: 24px;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if st.button("Sign Up", key="signup"):
    # Validation and sign-up logic
    if username and first_name and last_name and password:
        try:
            # Hash the password (add your own hashing method here)
            # hashed_password = hash_password(password)  # Use a suitable hashing method

            query = "INSERT INTO electronic_log.users (username, first_name, last_name, password_hash, role) VALUES (%s, %s, %s, %s, %s)"
            role = 'superuser' if is_superuser else 'user'
            cursor.execute(query, (username, first_name, last_name, password, role))
            conn.commit()

            st.success("Sign-up successful!")
            # Redirect to the login page
            login_button = st.button("Click here to login")

        except Exception as e:
            st.error(f"Error occurred during sign-up: {str(e)}")
    else:
        st.error("Please fill in all fields.")

# Sign-in link
st.markdown(
    '<p class="sign-in-link">Have an Account already? <a href="/npf_nccc_project/pages/1_login.py">Sign in</a></p>',
    unsafe_allow_html=True
)

import psycopg2
import streamlit as st

# Initialize session state
if 'session_state' not in st.session_state:
    st.session_state.session_state = {
        'username': None,
        'login_successful': False,
        'is_superuser': False
    }

st.title("Login")

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

cursor = conn.cursor()

username = st.text_input("Username")
password_input = st.text_input("Password", type="password")

if st.button("Login"):
    if username and password_input:
        try:
            query = "SELECT password_hash, role FROM electronic_log.users WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result:
                stored_password, role = result

                # Check password
                if password_input == stored_password:  # Direct comparison without hashing
                    st.session_state.session_state['username'] = username
                    st.session_state.session_state['login_successful'] = True
                    st.session_state.session_state['is_superuser'] = (role == 'superuser')

                    # Display success message
                    st.success(f"Login successful! Welcome, {username}")

                    # Redirect to the home page
                    st.experimental_rerun()  # Reload to reflect session state changes
                    
                else:
                    st.error("Invalid username or password.")
            else:
                st.error("Invalid username or password.")
                
        except Exception as e:
            st.error(f"Error occurred during login: {str(e)}")
    else:
        st.error("Please enter both username and password.")

# Sign-up link
st.markdown(
    '<p class="sign-in-link">Don’t have an account? <a href="/npf_nccc_project/pages/0_signup.py">Sign up</a></p>',
    unsafe_allow_html=True
)

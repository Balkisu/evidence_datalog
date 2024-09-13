from datetime import datetime
import psycopg2
import streamlit as st
import pandas as pd
from fpdf import FPDF

# Initialize session state if it doesn't exist
if 'session_state' not in st.session_state:
    st.session_state.session_state = {
        'login_successful': False,
        'username': "",
        'is_superuser': False
    }

def main():
    # Check if user is logged in
    if not st.session_state.session_state.get('login_successful', False):
        st.write("Session state: ", st.session_state)  # Debugging: Check session state
        st.warning("Please log in to access this page.")
        st.stop()

    # Display the home page
    st.title("Evidence Management System")
    st.write(f"Hello, {st.session_state.session_state.get('username', 'Guest')}. Use the sidebar to navigate through the different sections of the system.")
    
    if st.session_state.session_state.get('is_superuser', False):
        st.success("You are logged in as a Superuser!")

    # Add a sidebar for navigation
    st.sidebar.title("Navigation")
    menu_selection = st.sidebar.radio(
        "Go to", 
        ["Home", "Add Evidence", "View Evidence"]
    )

    # Handle navigation
    pages = {
        "Home": show_home,
        "Add Evidence": Add_Evidence,
        "View Evidence": View_Evidence,
    }
    
    if menu_selection in pages:
        pages[menu_selection]()

def show_home():
    st.header(f"Hello, {st.session_state.session_state.get('username', 'Guest')}.")
    
    if st.session_state.session_state.get('is_superuser', False):
        st.success("You are logged in as a Superuser!")

# Helper function to get a database connection
def get_db_connection():
    host = st.secrets["postgres"]["host"]
    port = st.secrets["postgres"]["port"]
    dbname = st.secrets["postgres"]["dbname"]
    user = st.secrets["postgres"]["user"]
    password = st.secrets["postgres"]["password"]

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        return conn
    except Exception as e:
        st.error(f"Error establishing database connection: {str(e)}")
        return None

    
def Add_Evidence():
    st.header("Add Evidence")

    # Assuming the user is logged in and their username is stored in session
    username = st.session_state.session_state.get('username')

    # Retrieve first and last name of the logged-in user from the database
    conn = get_db_connection()
    cursor = conn.cursor()

    user_query = """
    SELECT first_name, last_name
    FROM electronic_log.users
    WHERE username = %s
    """
    cursor.execute(user_query, (username,))
    user_result = cursor.fetchone()

    if user_result:
        first_name, last_name = user_result
    else:
        st.error("User information not found!")
        return

    # Form inputs for device details
    device_type = st.selectbox("Device Type", ["Smartphone", "Laptop", "Hard Drive", "Flash Drive", "Drone", "Other"])
    custom_device_type = ""
    if device_type == "Other":
        custom_device_type = st.text_input("Specify Device Type")

    make = st.text_input("Make (e.g., Samsung, Apple)")
    model = st.text_input("Model (e.g., iPhone 11 Pro Max)")
    color = st.text_input("Color")
    reference_number = st.text_input("Reference Number (Case Number)")
    description = st.text_area("Description of the Device", max_chars=150)
    serial_number = st.text_input("Serial Number")
    imei_number = st.text_input("IMEI Number (if applicable)")

    # Image upload
    front_image = st.file_uploader("Upload Front Image", type=["jpg", "jpeg", "png"])
    back_image = st.file_uploader("Upload Back Image", type=["jpg", "jpeg", "png"])

    # Password/Pattern input
    pin_password_pattern = st.text_input("PIN/Password/Pattern (if applicable)")

    # Form inputs for request-related details
    unit = st.text_input("Unit or Organization that owns the request")
    department = st.text_input("Department handling the request")
    investigator_name = st.text_input("Investigator Name")
    investigator_phone = st.text_input("Investigator Phone Number")
    date_of_use = st.date_input("Date and Time of Extraction", datetime.now())
    extraction_status = st.selectbox("Status of Extraction", ["Pending", "Processing", "Completed", "Released"])

    # Conditional fields based on status
    release_contact_name = None
    release_contact_phone = None
    release_date = None
    if extraction_status == "Released":
        release_contact_name = st.text_input("Name of the person the evidence was released to")
        release_contact_phone = st.text_input("Phone number of the person the evidence was released to")
        release_date = datetime.now()
        st.write(f"Release Date: {release_date}")

    # Submit button
    if st.button("Submit Evidence"):
        if reference_number and device_type and investigator_name:
            try:
                # Read image bytes
                front_image_data = front_image.read() if front_image else None
                back_image_data = back_image.read() if back_image else None

                # Insert into devices table (insert without exhibit_number for now)
                device_query = """
                INSERT INTO electronic_log.devices 
                (device_type, custom_device_type, make, model, color, reference_number, description, serial_number, imei_number, front_image, back_image, pin_password_pattern)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING device_id
                """
                cursor.execute(device_query, (device_type, custom_device_type, make, model, color, reference_number, description, serial_number, imei_number, front_image_data, back_image_data, pin_password_pattern))
                device_id = cursor.fetchone()[0]

                # Generate exhibit number after getting the device_id
                exhibit_number = generate_exhibit_number(device_type, first_name, last_name, device_id)

                # Now update the exhibit_number for this device
                update_exhibit_number_query = """
                UPDATE electronic_log.devices
                SET exhibit_number = %s
                WHERE device_id = %s
                """
                cursor.execute(update_exhibit_number_query, (exhibit_number, device_id))

                # Insert into requests table
                request_query = """
                INSERT INTO electronic_log.requests 
                (device_id, unit, department, investigator_name, investigator_phone, date_of_use, extraction_status, release_contact_name, release_contact_phone, release_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(request_query, (
                    device_id, unit, department, investigator_name, investigator_phone, date_of_use, extraction_status,
                    release_contact_name, release_contact_phone, release_date
                ))

                conn.commit()
                st.success("Evidence and request details added successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"Error adding evidence: {str(e)}")
            finally:
                cursor.close()
                conn.close()
        else:
            st.error("Please fill out all required fields.")

def generate_exhibit_number(device_type, first_name, last_name, device_id):
    # Map device types to abbreviations
    device_type_map = {
        "Smartphone": "SP",
        "Laptop": "L",
        "Hard Drive": "HD",
        "Flash Drive": "FD",
        "Drone": "D",
        "Other": "OTH"
    }
    
    # Get the current month and year
    now = datetime.now()
    month_year = now.strftime("%m%y")  # Format as MMYY

    # Get device abbreviation
    device_abbreviation = device_type_map.get(device_type, "OTH")

    # Get user initials
    user_initials = f"{first_name[0].upper()}{last_name[0].upper()}"

    # Generate exhibit number
    exhibit_number = f"NCCC/{device_abbreviation}/{month_year}/{user_initials}/{device_id}"
    
    return exhibit_number

# Clear form fields after submission
def clear_form():
    st.session_state.device_type = ""
    st.session_state.custom_device_type = ""
    st.session_state.make = ""
    st.session_state.model = ""
    st.session_state.color = ""
    st.session_state.reference_number = ""
    st.session_state.exhibit_number = ""
    st.session_state.description = ""
    st.session_state.serial_number = ""
    st.session_state.imei_number = ""
    st.session_state.front_image = None
    st.session_state.back_image = None
    st.session_state.pin_password_pattern = ""
    st.experimental_rerun()  # Reload the page to refresh form
    


def generate_pdf(evidence_record):
    """Generate a PDF report for a given evidence record."""
    pdf = FPDF()
    pdf.add_page()
    
    # Set title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, 'Evidence Report', ln=True, align='C')

    # Add the details from evidence_record
    pdf.set_font('Arial', '', 12)
    for key, value in evidence_record.items():
        pdf.cell(200, 10, f"{key}: {value}", ln=True)

    # Save the PDF to a file
    pdf_output = f"evidence_{evidence_record['Exhibit Number']}.pdf"
    pdf.output(pdf_output)
    return pdf_output

def View_Evidence():
    st.header("View Evidence")

    # Search bar for filtering evidence
    search_term = st.text_input("Search Evidence by Reference Number, Exhibit Number, or Investigator Name")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all evidence data along with requests info
    query = """
    SELECT 
        d.device_id, d.device_type, d.custom_device_type, d.make, d.model, d.color, d.reference_number, 
        d.exhibit_number, d.description, d.serial_number, d.imei_number, 
        r.unit, r.department, r.investigator_name, r.investigator_phone, r.date_of_use, 
        r.extraction_status, r.release_contact_name, r.release_contact_phone, r.release_date
    FROM 
        electronic_log.devices d
    JOIN 
        electronic_log.requests r ON d.device_id = r.device_id
    """
    
    cursor.execute(query)
    records = cursor.fetchall()

    # Define column headers
    columns = [
        "Device ID", "Device Type", "Custom Device Type", "Make", "Model", "Color", "Reference Number", 
        "Exhibit Number", "Description", "Serial Number", "IMEI Number", 
        "Unit", "Department", "Investigator Name", "Investigator Phone", "Date of Use", 
        "Extraction Status", "Release Contact Name", "Release Contact Phone", "Release Date"
    ]

    # Create a DataFrame for better search/filtering capabilities
    evidence_df = pd.DataFrame(records, columns=columns)

    # Filter based on search term
    if search_term:
        search_term = search_term.lower()
        evidence_df = evidence_df[
            evidence_df['Reference Number'].str.lower().str.contains(search_term) |
            evidence_df['Exhibit Number'].str.lower().str.contains(search_term) |
            evidence_df['Investigator Name'].str.lower().str.contains(search_term)
        ]

    # Display evidence in numbered rows
    st.subheader("Search Results:")
    for idx, row in evidence_df.iterrows():
        st.markdown(f"### {idx + 1}. Exhibit Number: {row['Exhibit Number']}")
        st.markdown(f"**Device Type:** {row['Device Type']} ({row['Custom Device Type']})")
        st.markdown(f"**Make:** {row['Make']} | **Model:** {row['Model']}")
        st.markdown(f"**Color:** {row['Color']}") 
        st.markdown(f"**Reference Number:** {row['Reference Number']}")
        st.markdown(f"**Serial Number:** {row['Serial Number']} | **IMEI Number:** {row['IMEI Number']}")
        st.markdown(f"**Unit:** {row['Unit']} | **Department:** {row['Department']}")
        st.markdown(f"**Investigator Name:** {row['Investigator Name']} | **Investigator Phone:** {row['Investigator Phone']}")
        st.markdown(f"**Date of Use:** {row['Date of Use']}")
        st.markdown(f"**Extraction Status:** {row['Extraction Status']}")
        st.markdown(f"**Release Contact Name:** {row['Release Contact Name']} | **Release Contact Phone:** {row['Release Contact Phone']}")
        st.markdown(f"**Release Date:** {row['Release Date']}")
        
        # Button to generate a PDF for this evidence record
        if st.button(f"Generate PDF for Exhibit {row['Exhibit Number']}", key=f"pdf_{row['Exhibit Number']}"):
            evidence_record = row.to_dict()
            pdf_file = generate_pdf(evidence_record)
            st.success(f"PDF generated for Exhibit {row['Exhibit Number']}.")
            with open(pdf_file, "rb") as file:
                st.download_button(
                    label=f"Download PDF for Exhibit {row['Exhibit Number']}",
                    data=file,
                    file_name=pdf_file,
                    mime="application/octet-stream"
                )
    st.markdown("---")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
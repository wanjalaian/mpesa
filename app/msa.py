import streamlit as st
import pdfplumber
import pandas as pd
import re

# Set the page layout to wide by default
st.set_page_config(layout="wide")

# Step 1: Center the content on the page
st.markdown("""
    <style>
        .main {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            flex-direction: column;
            max-width: 1440px;
            margin-left: auto;
            margin-right: auto;
        }
    </style>
""", unsafe_allow_html=True)

# Create a page selector (radio buttons or selectbox)
page_selection = st.radio("Select Page", ("Data", "Analysis"))

# Title based on selected page
if page_selection == "Data":
    st.title('M-PESA Statement Data')
elif page_selection == "Analysis":
    st.title('M-PESA Statement Analysis')

# Upload the PDF file
uploaded_file = st.file_uploader("Upload your PDF statement", type='pdf')

if uploaded_file:
    # Open the uploaded PDF with pdfplumber
    with pdfplumber.open(uploaded_file) as pdf:
        all_data = []  # List to hold all extracted tables
        summary_table = None
        transaction_data = pd.DataFrame()  # Empty DataFrame to hold combined transaction data
        statement_verification_code = None  # Variable to hold the Statement Verification Code
        customer_name = None
        mobile_number = None
        email_address = None
        statement_period = None
        request_date = None
        
        # Extract text from the first page for customer info
        first_page = pdf.pages[0]
        first_page_text = first_page.extract_text()
        
        if first_page_text:
            # Regex patterns for each piece of customer info
            name_pattern = r'Customer Name:\s*([A-Za-z\s]+)'  # Capture name in proper case
            mobile_pattern = r'Mobile Number:\s*(\d{10})'  # Capture mobile number
            email_pattern = r'Email Address:\s*([a-zA-Z0-9@.]+)'  # Capture email
            period_pattern = r'Statement Period:\s*(\d{1,2}\s\w+\s\d{4})\s*-\s*(\d{1,2}\s\w+\s\d{4})' # Capture statement period
            date_pattern = r'Request Date:\s*(\d{1,2}\s\w+\s\d{4})'  # Capture request date (e.g. "19 Nov 2024")
            
            # Extract data using regex
            name_match = re.search(name_pattern, first_page_text)
            if name_match:
                customer_name = name_match.group(1).title().replace('Null', '').replace('Mobile Number', '').strip()  # Capitalize the name and remove "null"

            mobile_match = re.search(mobile_pattern, first_page_text)
            if mobile_match:
                mobile_number = "+254" + mobile_match.group(1)[1:]  # Replace first 0 with +254

            email_match = re.search(email_pattern, first_page_text)
            if email_match:
                email_address = email_match.group(1).lower()  # Convert to lowercase

            period_match = re.search(period_pattern, first_page_text)
            if period_match:
                start_date = period_match.group(1)  # Capture start date
                end_date = period_match.group(2)    # Capture end date
                statement_period = f"{start_date} - {end_date}"  # Format as range

            date_match = re.search(date_pattern, first_page_text)
            if date_match:
                request_date = date_match.group(1)  # Capture the date (e.g., "19 Nov 2024")

        # Extract tables from each page and process them
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()

            for table in tables:
                # If this table is identified as the summary table (first page, first table)
                if page_num == 0 and summary_table is None:
                    summary_table = pd.DataFrame(table[1:], columns=table[0])  # First table as summary
                else:
                    # For other pages, treat as a transaction table (assuming structure remains the same)
                    # Skip the first row (header) and add the rest to the transaction_data
                    temp_df = pd.DataFrame(table[1:], columns=table[0])

                    # Ensure the last column is 'Balance'
                    temp_df.columns = list(temp_df.columns[:-1]) + ['Balance']
                    
                    # Remove rows with None or blank values
                    temp_df.dropna(how='any', inplace=True)  # Drop any row with None/NaN values
                    
                    # Add the data to the transaction_data
                    transaction_data = pd.concat([transaction_data, temp_df], ignore_index=True)

        # Fetch text from the last page for Statement Verification Code
        last_page = pdf.pages[-1]
        last_page_text = last_page.extract_text()

        # Look for the Statement Verification Code in the last page's text
        if last_page_text:
            match = re.search(r'\b[A-Z0-9]{8}\b', last_page_text)  # Looking for 8 uppercase alphanumeric characters
            if match:
                statement_verification_code = match.group(0)

        # Step 2: Clean up the transaction_data
        # Drop the unwanted extra column after Balance (if it exists)
        if 'Statement Verification Code' in transaction_data.columns:
            transaction_data.drop(columns=['Statement Verification Code'], inplace=True)

    # Page-specific Content
    if page_selection == "Data":
        # Step 3: Display Customer Information and Transaction Summary Side by Side
        
        col1, col2 = st.columns([2, 3]) 
        # Display Customer Information on the left
        with col1:
            st.subheader("Customer Information")
            if customer_name:
                st.write(f"**Customer Name:** {customer_name}")
            if mobile_number:
                st.write(f"**Mobile Number:** {mobile_number}")
            if email_address:
                st.write(f"**Email Address:** {email_address}")
            if statement_period:
                st.write(f"**Statement Period:** {statement_period}")
            if request_date:
                st.write(f"**Request Date:** {request_date}")
            st.write(f"**Statement Currency:** Kenya Shillings (Ksh.)")

            # Display Statement Verification Code in bold below customer info
            if statement_verification_code:
                st.markdown(f"**Statement Verification Code:** {statement_verification_code}")  # Display in bold

        # Display the Summary Table and Transaction Data on the right
        with col2:
            if summary_table is not None:
                st.subheader("Summary Table")
                st.dataframe(summary_table)  # Display the summary table

        # Step 4: Display the Combined Transaction Data
        if not transaction_data.empty:
            st.subheader("Transaction Table")
            st.dataframe(transaction_data)  # Display the combined transaction table
        else:
            st.warning("No transaction data found.")

    elif page_selection == "Analysis":
        # Analysis Page Content: You can add your analysis code here
        st.subheader("Analysis Page")
        st.write("This section is for analysis of the M-PESA statement data.")
        # Example analysis (this is where you can add your actual analysis logic):
        if not transaction_data.empty:
            st.write("Here is some sample analysis based on the transaction data:")
            # Example: Displaying basic transaction summary
            st.write(transaction_data.describe())

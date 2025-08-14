import streamlit as st
import pdfplumber
import pandas as pd
import re
import numpy as np
from streamlit_dynamic_filters import DynamicFilters
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Home", layout="wide")

# --- App Title and Description ---
st.title("M-PESA Transaction Analyzer")
st.markdown("""
Welcome to the M-PESA Transaction Analyzer!

This application helps you analyze your M-PESA statements to gain insights into your spending and income.

**Instructions:**
1.  Upload your M-PESA statement in PDF format (ensure it is not password protected).
2.  View a summary of your transactions and detailed reports.
""")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your PDF statement", type="pdf")

if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file
else:
    uploaded_file = st.session_state.get("uploaded_file")

# The rest of the code is the processing logic from 1_📎 Upload Your Statement.py
# I will copy it from the classification_table onwards.

classification_table = pd.DataFrame([
    {"Details Pattern": "Withdrawal Charge", "Category": "Charges (Agent Withdrawal)", "Description": "Agent withdrawal charges."},
    {"Details Pattern": "Send Money Reversal", "Category": "Reversal Money In", "Description": "Money received from a reversal transaction."},
    {"Details Pattern": "Salary Payment from", "Category": "Money In From Bank", "Description": "Money received from NCBA Bank transfers (e.g., salary or other payments)."},
    {"Details Pattern": "Receive International Zero Rated Transfer", "Category": "Money In (Other)", "Description": "Money received from international sources."},
    {"Details Pattern": "Promotion Payment from", "Category": "Money In (Promotion)", "Description": "Money received from betting winnings (e.g., Betika)."},
    {"Details Pattern": "Pay Merchant Charge", "Category": "Charges (Till)", "Description": "Charges for payments to merchants."},
    {"Details Pattern": "Pay Utility Reversal", "Category": "Reversal Money In", "Description": "Money received from a reversal of utility payments."},
    {"Details Pattern": "Pay Bill to", "Category": "Business Spending (Paybill)", "Description": "Payments made to PayBill numbers (e.g., KPLC, utilities, services)."},
    {"Details Pattern": "Pay Bill Fuliza M-Pesa to", "Category": "Fuliza Spending (Business Paybill)", "Description": "Payments made to PayBill numbers using Fuliza overdraft (e.g., KPLC, utilities, services)."},
    {"Details Pattern": "Pay Bill Online Fuliza M-Pesa to", "Category": "Fuliza Spending (Business Paybill)", "Description": "Payments made to PayBill numbers using Fuliza overdraft (e.g., KPLC, utilities, services)."},
    {"Details Pattern": "Pay Bill Charge", "Category": "Charges (Paybill)", "Description": "Transaction fees for Paybill payments."},
    {"Details Pattern": "Pay Bill Online to", "Category": "Business Spending (Paybill)", "Description": "Payments made to PayBill numbers"},
    {"Details Pattern": "Overdraft of Credit Party", "Category": "Fuliza Money In", "Description": "Fuliza overdraft used."},
    {"Details Pattern": "OD Loan Repayment", "Category": "Fuliza Deduction", "Description": "Repayment of Fuliza overdraft loans."},
    {"Details Pattern": "Merchant Payment", "Category": "Business Spending (Till)", "Description": "Payments to businesses via M-Pesa till numbers."},
    {"Details Pattern": "Merchant Customer Payment", "Category": "Money In From Till", "Description": "Payments from businesses via M-Pesa till numbers."},
    {"Details Pattern": "Merchant Payment Online to", "Category": "Business Spending (Till)", "Description": "Payments made online to businesses via till numbers."},
    {"Details Pattern": "Merchant Payment Fuliza", "Category": "Fuliza Spending (Till)", "Description": "Payments to businesses using Fuliza overdraft."},
    {"Details Pattern": "M-Shwari Withdraw", "Category": "M-Shwari Withdrawal", "Description": "Withdrawals from M-Shwari savings."},
    {"Details Pattern": "M-Shwari Deposit", "Category": "M-Shwari Deposit", "Description": "Deposits to M-Shwari savings."},
    {"Details Pattern": "M-Shwari Lock Activate and Save", "Category": "Deposit to M-Shwari Locked Savings", "Description": "Transfers made to M-Shwari locked savings accounts."},
    {"Details Pattern": "Funds received from", "Category": "Funds From Individual", "Description": "Money sent by individuals."},
    {"Details Pattern": "Customer Withdrawal At Agent Till", "Category": "Agent Withdrawals", "Description": "Withdrawals made at M-Pesa agent tills."},
    {"Details Pattern": "Customer Transfer to", "Category": "Send Money to Individual", "Description": "Money sent to individuals."},
    {"Details Pattern": "Customer Transfer of Funds Charge", "Category": "Charges (Send Money)", "Description": "Transaction fees for transferring money to individuals."},
    {"Details Pattern": "Customer Transfer Fuliza MPesa", "Category": "Fuliza Funds to Individual", "Description": "Money sent to individuals using Fuliza overdraft."},
    {"Details Pattern": "Customer Transfer Fuliza M-Pesa", "Category": "Fuliza Funds to Individual", "Description": "Money sent to individuals using Fuliza overdraft."},
    {"Details Pattern": "Customer Send Money to Micro SME Business", "Category": "Pochi La Biashara", "Description": "Payments to small businesses using Fuliza overdraft."},
    {"Details Pattern": "Customer Payment to Small Business", "Category": "Pochi La Biashara", "Description": "Payments to small businesses (Pochi La Biashara)."},
    {"Details Pattern": "Customer Bundle Purchase with Fuliza", "Category": "Fuliza Airtime Purchase", "Description": "Data bundles purchased using Fuliza overdraft."},
    {"Details Pattern": "Customer Bundle Purchase", "Category": "Airtime/Data Spending", "Description": "Data bundles purchased online."},
    {"Details Pattern": "Buy Bundles Online", "Category": "Airtime/Data Spending", "Description": "Online purchase of bundles."},
    {"Details Pattern": "Buy Bundles", "Category": "Airtime/Data Spending", "Description": "Offline purchase of bundles."},
    {"Details Pattern": "Business Payment from", "Category": "Money In From Bank", "Description": "Money received from KCB Bank."},
    {"Details Pattern": "Airtime Purchase with Fuliza", "Category": "Fuliza Airtime Purchase", "Description": "Airtime purchased using Fuliza overdraft."},
    {"Details Pattern": "Airtime Purchase", "Category": "Airtime/Data Spending", "Description": "Regular airtime purchase."},
    {"Details Pattern": "Airtime Purchase Reversal", "Category": "Reversal Money In", "Description": "Regular airtime purchase."},
    {"Details Pattern": "Offnet B2C Transfer by", "Category": "Money In from Airtel Money", "Description": "Money sent from Airtel Money."},
    {"Details Pattern": "Offnet C2B Transfer to 585555", "Category": "Send to Airtel Money", "Description": "Airtel Money purchase."},
    {"Details Pattern": "Uncategorized", "Category": "Uncategorized", "Description": "Transactions without details or with unrecognized patterns."},
    {"Details Pattern": "Deposit of Funds at Agent Till", "Category": "M-Pesa Agent Deposit", "Description": "Deposits at M-PESA Agents."},
    {"Details Pattern": "Small Business Payment to", "Category": "Money in From Pochi La Biashara", "Description": "Money in from small business."},
    {"Details Pattern": "Business Payment", "Category": "Money in From Business Till", "Description": "Money in from small business."},
    {"Details Pattern": "M-KOPA", "Category": "M-Kopa Payment", "Description": "Payment for hire purchase device."}
])

def clean_details(details):
    # Remove line breaks based on the space conditions
    details = re.sub(r'(?<=\s)\n', '', details)  # Remove line breaks after spaces
    details = re.sub(r'(?<!\s)\n', ' ', details)  # Add a space before line breaks without space

    # Remove carriage returns
    details = details.replace("\r", "")

    # Convert to lowercase
    details = details.lower()
    
    return details

def infer_category(details):
    details = clean_details(details)  # Clean the details first
    
    # Now, proceed with the categorization logic as before
    for _, row in classification_table.iterrows():
        pattern = row["Details Pattern"].lower()
        if pattern in details:
            category = row["Category"]
            # Reclassification logic for "M-Kopa Payment"
            if "paybill" in category.lower() and "m-kopa" in details:
                return "M-Kopa Payment"
            return category

    return "Uncategorized"


if uploaded_file:
    # Open the uploaded PDF with pdfplumber
    with pdfplumber.open(uploaded_file) as pdf:
        all_data = []
        summary_table = None
        transaction_data = pd.DataFrame()
        statement_verification_code = None
        customer_name = None
        mobile_number = None
        email_address = None
        statement_period = None
        request_date = None
        statement_age = None

        # Extract text from the first page for customer info
        first_page = pdf.pages[0]
        first_page_text = first_page.extract_text()

        if first_page_text:
            # Extract customer information using regex patterns
            name_pattern = r"Customer Name:\s*([A-Za-z\s]+)"
            mobile_pattern = r"Mobile Number:\s*(\d{10})"
            email_pattern = r"Email Address:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            period_pattern = r"Statement Period:\s*(\d{1,2}\s\w+\s\d{4})\s*-\s*(\d{1,2}\s\w+\s\d{4})"
            date_pattern = r"Request Date:\s*(\d{1,2}\s\w+\s\d{4})"

            name_match = re.search(name_pattern, first_page_text)
            if name_match:
                customer_name = name_match.group(1).title().replace("Null", "").replace("Mobile Number", "").strip()

            mobile_match = re.search(mobile_pattern, first_page_text)
            if mobile_match:
                mobile_number = "+254" + mobile_match.group(1)[1:]

            email_match = re.search(email_pattern, first_page_text)
            if email_match:
                email_address = email_match.group(1).lower()

            period_match = re.search(period_pattern, first_page_text)
            if period_match:
                start_date = period_match.group(1)
                end_date = period_match.group(2)
                statement_period = f"{start_date} - {end_date}"

            date_match = re.search(date_pattern, first_page_text)
            if date_match:
                request_date = date_match.group(1)
            if request_date:
                try:
                    # Parse the request_date string into a datetime object
                    request_date_obj = datetime.strptime(request_date, "%d %b %Y")
                    # Calculate the difference between the current date and the request date
                    current_date = datetime.now()
                    statement_age = (current_date - request_date_obj).days
                except ValueError:
                    statement_age = "Invalid Request Date Format"

        # Extract tables from each page and process them
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()

            for table in tables:
                if page_num == 0 and summary_table is None:
                    summary_table = pd.DataFrame(table[1:], columns=table[0])
                else:
                    temp_df = pd.DataFrame(table[1:], columns=table[0])
                    temp_df.columns = list(temp_df.columns[:-1]) + ["Balance"]
                    temp_df.dropna(how="any", inplace=True)
                    transaction_data = pd.concat([transaction_data, temp_df], ignore_index=True)

        # Fetch text from the last page for statement verification code
        last_page = pdf.pages[-1]
        last_page_text = last_page.extract_text()

        if last_page_text:
            # Search for "Statement Verification Code" and capture the next line
            match = re.search(r"Statement Verification Code[\s\S]*?([A-Z0-9]{8})", last_page_text)
            if match:
                statement_verification_code = match.group(1)
        
        # Clean up the transaction data
        def safe_convert_to_float(x):
            if pd.notna(x) and str(x)!= "":
                try:
                    return float(str(x).replace(",", "").replace("Ksh ", ""))
                except ValueError:
                    return np.nan
            else:
                return np.nan

        if "Paid In" in transaction_data.columns:
            transaction_data["Paid In"] = transaction_data["Paid In"].apply(safe_convert_to_float)
        if "Withdrawn" in transaction_data.columns:
            transaction_data["Withdrawn"] = transaction_data["Withdrawn"].apply(safe_convert_to_float)
        if "Balance" in transaction_data.columns:
            transaction_data["Balance"] = transaction_data["Balance"].apply(safe_convert_to_float)

        if "Statement Verification Code" in transaction_data.columns:
            transaction_data.drop(columns=["Statement Verification Code"], inplace=True)

    # Display customer information and transaction summary side by side
    col1, col2 = st.columns([2, 3])

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
        if statement_age is not None:
            st.write(f"**Statement Age:** {statement_age} days")
        st.write("**Statement Currency:** Kenya Shillings (Ksh.)")
        
        if statement_verification_code:
            st.markdown(f"**Statement Verification Code:** {statement_verification_code}")

    with col2:
        if summary_table is not None:
            st.subheader("Summary Table")
            st.dataframe(summary_table)

    # Display the combined transaction data
    if not transaction_data.empty:
        st.subheader("Transaction Table")
        st.dataframe(transaction_data)

        # Save original DataFrame to a CSV
        transaction_data.to_csv("original_transactions.csv", index=False)

        # Separate incoming and outgoing transactions
        incoming_transactions = transaction_data[transaction_data["Paid In"].notna()].copy()
        incoming_transactions.drop(columns=["Balance", "Withdrawn"], inplace=True)
        incoming_transactions["Category"] = incoming_transactions["Details"].apply(infer_category)

        outgoing_transactions = transaction_data[transaction_data["Withdrawn"].notna()].copy()
        outgoing_transactions.drop(columns=["Balance", "Paid In", "Transaction Status"], inplace=True)
        outgoing_transactions["Category"] = outgoing_transactions["Details"].apply(infer_category)

        # Calculate transaction counts
        incoming_count = len(incoming_transactions)
        outgoing_count = len(outgoing_transactions)

        st.subheader(f"Incoming Transactions - {incoming_count:,}")
        st.dataframe(incoming_transactions)

        st.subheader(f"Outgoing Transactions - {outgoing_count:,}")
        st.dataframe(outgoing_transactions)
        


        receive_keywords = ["Funds received from -"]
        send_keywords = ["Customer Transfer Fuliza MPesa", "Customer Transfer to -"]

        
        # Store in session state
        st.session_state["transaction_data"] = transaction_data
        st.success("Transaction data has been successfully loaded!")

        #if "incoming_transactions" not in st.session_state:
        st.session_state["incoming_transactions"] = incoming_transactions

        #if "outgoing_transactions" not in st.session_state:
        st.session_state["outgoing_transactions"] = outgoing_transactions  

   

    else:
        st.warning("No transaction data found.")
else:
    st.info("Please upload a PDF statement to proceed.")
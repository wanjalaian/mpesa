import streamlit as st

if "transaction_data" not in st.session_state:
    st.warning("Please upload your statement on the Home page first.")
    st.stop()
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

transaction_data = st.session_state["transaction_data"]
incoming_transactions = st.session_state["incoming_transactions"]
outgoing_transactions = st.session_state["outgoing_transactions"]

# Convert all negative values in the 'Withdrawn' column to positive
outgoing_transactions["Withdrawn"] = outgoing_transactions["Withdrawn"].abs()


# Overview Section: Insights Table
st.header("Overview")

# Calculate Total Transactions
total_transactions = transaction_data.shape[0]

# Calculate Total Incoming and Outgoing
total_incoming = incoming_transactions["Paid In"].sum()
total_outgoing = outgoing_transactions["Withdrawn"].abs().sum()

# Top 5 Categories by Volume
incoming_top_categories_by_volume = (
    incoming_transactions["Category"]
    .value_counts()
    .head(5)
    .reset_index()
    .rename(columns={"index": "Category", "Category": "Category", "count":"Number of Transactions"})
)

outgoing_top_categories_by_volume = (
    outgoing_transactions["Category"]
    .value_counts()
    .head(5)
    .reset_index()
    .rename(columns={"index": "Category", "Category": "Category", "count":"Number of Transactions"})
)

# Top 5 Categories by Value
incoming_top_categories_by_value = (
    incoming_transactions.groupby("Category")["Paid In"].sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
    .rename(columns={"Paid In": "Amount"})
)

# Format incoming values to two decimal places
incoming_top_categories_by_value["Amount"] = incoming_top_categories_by_value["Amount"].apply(lambda x: f"{x:,.2f}")

outgoing_top_categories_by_value = (
    outgoing_transactions.groupby("Category")["Withdrawn"].sum()
    .abs()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
    .rename(columns={"Withdrawn": "Amount"})
)

# Format outgoing values to two decimal places
outgoing_top_categories_by_value["Amount"] = outgoing_top_categories_by_value["Amount"].apply(lambda x: f"{x:,.2f}")


# Display Summary Insights
st.subheader("Insights")
st.write(f"**Total Transactions:** {total_transactions}")
st.write(f"**Total Incoming Transactions:** KSh. {total_incoming:,.2f}")
st.write(f"**Total Outgoing Transactions:** KSh. {total_outgoing:,.2f}")

# Display Top 5 Categories by Volume and Value side by side
col1, col2 = st.columns(2)

with col1:
    st.write("### Top 5 Incoming Categories by Volume")
    st.table(incoming_top_categories_by_volume)

with col2:
    st.write("### Top 5 Outgoing Categories by Volume")
    st.table(outgoing_top_categories_by_volume)

col3, col4 = st.columns(2)

with col3:
    st.write("### Top 5 Incoming Categories by Value")
    st.table(incoming_top_categories_by_value)

with col4:
    st.write("### Top 5 Outgoing Categories by Value")
    st.table(outgoing_top_categories_by_value)

# Add a dropdown to let the user select the time period for grouping
time_period = st.selectbox(
    "Select Time Period",
    ("Daily", "Monthly", "6 Months", "Yearly"),
    index=0  # Default is Daily
)

# Convert 'Completion Time' to datetime format if it's not already
incoming_transactions['Completion Time'] = pd.to_datetime(incoming_transactions['Completion Time'], errors='coerce')
outgoing_transactions['Completion Time'] = pd.to_datetime(outgoing_transactions['Completion Time'], errors='coerce')


# Function to group data based on selected time period
def group_transactions_by_time_period(df, time_period):
    if time_period == "Daily":
        # Group by day
        return df.groupby(df['Completion Time'].dt.date).size().reset_index(name='Transaction Count')
    elif time_period == "Monthly":
        # Group by month (convert Period to string)
        df['Month'] = df['Completion Time'].dt.to_period('M').astype(str)
        return df.groupby('Month').size().reset_index(name='Transaction Count')
    elif time_period == "6 Months":
        # Group by 6 months (using custom period)
        df['6 Months Period'] = df['Completion Time'].dt.to_period("M").apply(lambda x: f"{x.year}-{(x.month-1)//6+1}H")
        return df.groupby('6 Months Period').size().reset_index(name='Transaction Count')
    elif time_period == "Yearly":
        # Group by year and ensure the year is displayed as an integer
        df['Year'] = df['Completion Time'].dt.year
        return df.groupby('Year').size().reset_index(name='Transaction Count')

# Group incoming and outgoing transactions based on selected time period
incoming_grouped = group_transactions_by_time_period(incoming_transactions, time_period)
outgoing_grouped = group_transactions_by_time_period(outgoing_transactions, time_period)

# Plot the grouped data
fig = go.Figure()

# Add Incoming Transactions to the plot
fig.add_trace(go.Scatter(x=incoming_grouped.iloc[:, 0], y=incoming_grouped['Transaction Count'],
                         mode='lines+markers', name='Incoming Transactions'))

# Add Outgoing Transactions to the plot
fig.add_trace(go.Scatter(x=outgoing_grouped.iloc[:, 0], y=outgoing_grouped['Transaction Count'],
                         mode='lines+markers', name='Outgoing Transactions'))

# Update layout
fig.update_layout(
    title=f"Transaction Volume Over Time ({time_period})",
    xaxis_title=time_period,
    yaxis_title="Number of Transactions",
    template="plotly_dark",
    legend_title="Transaction Type",
    hovermode="closest"
)

# Display the plot
st.plotly_chart(fig)


# Create two columns for side-by-side pie charts
col1, col2 = st.columns(2)

# Pie Chart for Money In (Incoming Transactions)
with col1:
    
    money_in_pie = px.pie(
        incoming_transactions,
        names="Category",
        values="Paid In",
        title="Distribution of Money In by Category",
        template="plotly_dark",
        hole=0.4  # For a donut-style chart
    )
    st.plotly_chart(money_in_pie)

# Pie Chart for Money Out (Outgoing Transactions)
with col2:
    
    money_out_pie = px.pie(
        outgoing_transactions,
        names="Category",
        values=outgoing_transactions["Withdrawn"].abs(),  # Convert to positive
        title="Distribution of Money Out by Category",
        template="plotly_dark",
        hole=0.4  # For a donut-style chart
    )
    st.plotly_chart(money_out_pie)


# Define the keywords for send and receive money transactions
send_keywords = ["Customer Transfer Fuliza MPesa", "Customer Transfer to -"]
receive_keywords = ["Funds received from -"]

# Function to classify transactions based on keywords
def classify_transactions(df, keywords, transaction_type):
    # Search for the keywords in the 'Details' column
    if transaction_type == 'send':
        return df[df['Details'].str.contains('|'.join(keywords), case=False, na=False)]
    elif transaction_type == 'receive':
        return df[df['Details'].str.contains('|'.join(keywords), case=False, na=False)]

# Classify incoming transactions as "Receive" based on the defined receive_keywords
incoming_transactions_filtered = classify_transactions(incoming_transactions, receive_keywords, 'receive')

# Classify outgoing transactions as "Send" based on the defined send_keywords
outgoing_transactions_filtered = classify_transactions(outgoing_transactions, send_keywords, 'send')

# Function to extract and format names from the Details column

def extract_name(details):
    # Replace line breaks with a space
    details = re.sub(r'\n', ' ', details)
    
    # Use re.DOTALL to make . match newline characters
    match = re.search(r'\d{3}\*\*\*\*\*\*\d{3}\s+(.*)', details, re.DOTALL)
    if match:
        # Extract the name, strip any leading/trailing whitespace, and format it to title case
        name = match.group(1).strip().title()
        return name
    return None  # Return None if no match is found

# Apply the extraction function to the Details column for outgoing transactions
outgoing_transactions_filtered['Recipient'] = outgoing_transactions_filtered['Details'].apply(extract_name)

# Apply the extraction function to the Details column for incoming transactions
incoming_transactions_filtered['Sender'] = incoming_transactions_filtered['Details'].apply(extract_name)

# Get the top 10 destinations (recipients) for incoming transactions by amount

top_recipients_by_amount = (
    outgoing_transactions_filtered.groupby('Recipient')['Withdrawn']
    .sum()
    .abs()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
    .rename(columns={"Withdrawn": "Total Amount"})
)

# Get the top 10 sources (senders) for outgoing transactions by amount
top_senders_by_amount = (
    incoming_transactions_filtered.groupby('Sender')['Paid In']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
    .rename(columns={"Paid In": "Total Amount"})
)

# Format the amounts to two decimal places
top_senders_by_amount["Total Amount"] = top_senders_by_amount["Total Amount"].apply(lambda x: f"{x:,.2f}")
top_recipients_by_amount["Total Amount"] = top_recipients_by_amount["Total Amount"].apply(lambda x: f"{x:,.2f}")


# Create two columns to display the tables side by side
col1, col2 = st.columns(2)

# Display the top senders in the first column
with col1:
    st.write("### Top 10 Senders by Amount")
    st.dataframe(top_senders_by_amount)

# Display the top recipients in the second column
with col2:
    st.write("### Top 10 Recipients by Amount")
    st.dataframe(top_recipients_by_amount)
		


# Extract time components
incoming_transactions['Hour'] = incoming_transactions['Completion Time'].dt.hour
incoming_transactions['Day of Week'] = incoming_transactions['Completion Time'].dt.dayofweek
incoming_transactions['Month'] = incoming_transactions['Completion Time'].dt.month

outgoing_transactions['Hour'] = outgoing_transactions['Completion Time'].dt.hour
outgoing_transactions['Day of Week'] = outgoing_transactions['Completion Time'].dt.dayofweek
outgoing_transactions['Month'] = outgoing_transactions['Completion Time'].dt.month

# Group by time components and sum the amounts
incoming_hourly = incoming_transactions.groupby(['Day of Week', 'Hour'])['Paid In'].sum().unstack().fillna(0)
outgoing_hourly = outgoing_transactions.groupby(['Day of Week', 'Hour'])['Withdrawn'].sum().abs().unstack().fillna(0)

# Create a heatmap for hourly incoming patterns
fig_incoming_hourly = go.Figure(data=go.Heatmap(
    z=incoming_hourly.values,
    x=incoming_hourly.columns,
    y=incoming_hourly.index.map({0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}),
    colorscale='Blues',
    name='Incoming Transactions'
))

fig_incoming_hourly.update_layout(
    title="Hourly Incoming Transactions",
    xaxis_title="Hour of the Day",
    yaxis_title="Day of the Week",
    template="plotly_dark",
    legend_title="Transaction Type"
)

# Create a heatmap for hourly outgoing patterns
fig_outgoing_hourly = go.Figure(data=go.Heatmap(
    z=outgoing_hourly.values,
    x=outgoing_hourly.columns,
    y=outgoing_hourly.index.map({0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}),
    colorscale='Reds',
    name='Outgoing Transactions'
))

fig_outgoing_hourly.update_layout(
    title="Hourly Outgoing Transactions",
    xaxis_title="Hour of the Day",
    yaxis_title="Day of the Week",
    template="plotly_dark",
    legend_title="Transaction Type"
)

col1, col2 = st.columns(2)

with col1:
    #st.write("### Hourly Incoming Transactions")
    st.plotly_chart(fig_incoming_hourly)

with col2:
    #st.write("### Hourly Outgoing Transactions")
    st.plotly_chart(fig_outgoing_hourly)

# Ensure the 'Completion Time' column is in datetime format
transaction_data['Completion Time'] = pd.to_datetime(transaction_data['Completion Time'], errors='coerce')

# Sort the transactions by completion time
transaction_data = transaction_data.sort_values(by='Completion Time')

# Create a line chart for the account balance over time
fig_balance = go.Figure()

fig_balance.add_trace(go.Scatter(
    x=transaction_data['Completion Time'],
    y=transaction_data['Balance'],
    mode='lines+markers',
    name='Account Balance'
))

fig_balance.update_layout(
    title="Account Balance Over Time",
    xaxis_title="Date",
    yaxis_title="Balance",
    template="plotly_dark",
    legend_title="Transaction Type"
)


st.plotly_chart(fig_balance)

# Define the charges categories
charges_categories = ["Charges (Till)", "Charges (Send Money)", "Charges (Paybill)"]

# Filter charges transactions
charges_transactions = outgoing_transactions[outgoing_transactions['Category'].isin(charges_categories)]

# Group the charges transactions by month and category
charges_grouped = charges_transactions.groupby([pd.Grouper(key='Completion Time', freq='M'), 'Category'])['Withdrawn'].sum().reset_index()

# Group the non-charges transactions by month and category
non_charges_transactions = outgoing_transactions[~outgoing_transactions['Category'].isin(charges_categories)]
#non_charges_grouped = non_charges_transactions.groupby([pd.Grouper(key='Completion Time', freq='M'), 'Category'])['Withdrawn'].sum().reset_index()

# Convert negative values to positive
charges_grouped['Withdrawn'] = charges_grouped['Withdrawn'].abs()

# Create a stacked bar chart
fig_charges = px.bar(
    charges_grouped,
    x='Completion Time',
    y='Withdrawn',
    color='Category',
    barmode='stack',
    title="Charges Breakdown Over Time",
    labels={'Completion Time': 'Month', 'Withdrawn': 'Amount', 'Category': 'Transaction Category'},
    template="plotly_dark"
)


st.plotly_chart(fig_charges)

# Combine the transactions into a single dataframe
categorized_transactions = pd.concat([incoming_transactions, outgoing_transactions])

# Extract time components
categorized_transactions['Completion Time'] = pd.to_datetime(categorized_transactions['Completion Time'], errors='coerce')
categorized_transactions['Day of Week'] = categorized_transactions['Completion Time'].dt.dayofweek
categorized_transactions['Month'] = categorized_transactions['Completion Time'].dt.to_period('M').astype(str)
categorized_transactions['Year'] = categorized_transactions['Completion Time'].dt.to_period('Y').astype(str)

# Group by category and time period
def group_transactions_by_time(df, time_period):
    if time_period == "Daily":
        return df.groupby(['Category', 'Day of Week'])['Paid In'].sum().unstack().fillna(0)
    elif time_period == "Monthly":
        return df.groupby(['Category', 'Month'])['Paid In'].sum().unstack().fillna(0)
    elif time_period == "Yearly":
        return df.groupby(['Category', 'Year'])['Paid In'].sum().unstack().fillna(0)

# Add a dropdown to let the user select the time period
time_period = st.selectbox(
    "Select Time Period",
    ("Daily", "Monthly", "Yearly"),
    index=0  # Default is Daily
)

# Group the transactions based on the selected time period
frequency_data = group_transactions_by_time(categorized_transactions, time_period)

# Create the heatmap
fig = go.Figure(data=go.Heatmap(
    z=frequency_data.values,
    x=frequency_data.columns.map({0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}) if time_period == "Daily" else frequency_data.columns,
    y=frequency_data.index,
    colorscale='Blues',
    name='Transaction Amount'
))

# Update layout
fig.update_layout(
    title=f"Transaction Amount by {time_period} Category",
    xaxis_title=time_period,
    yaxis_title="Category",
    template="plotly_dark"
)

# Display the heatmap
st.subheader("Transaction Amount Analysis")

st.plotly_chart(fig)
		
# Extract time components
categorized_transactions['Completion Time'] = pd.to_datetime(categorized_transactions['Completion Time'], errors='coerce')
categorized_transactions = categorized_transactions.sort_values(by='Completion Time')

# Calculate cumulative sums
categorized_transactions['Cumulative Paid In'] = categorized_transactions['Paid In'].cumsum()
categorized_transactions['Cumulative Withdrawn'] = categorized_transactions['Withdrawn'].cumsum()

# Create the area chart
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=categorized_transactions['Completion Time'],
    y=categorized_transactions['Cumulative Paid In'],
    mode='lines',
    name='Cumulative Receiving',
    fill='tozeroy',  # Fill area under the line
    line=dict(color='blue')
))

fig.add_trace(go.Scatter(
    x=categorized_transactions['Completion Time'],
    y=categorized_transactions['Cumulative Withdrawn'],
    mode='lines',
    name='Cumulative Spending',
    fill='tozeroy',  # Fill area under the line
    line=dict(color='red')
))

# Update layout
fig.update_layout(
    title="Cumulative Spending vs. Receiving Over Time",
    xaxis_title="Date",
    yaxis_title="Amount",
    template="plotly_dark",
    legend_title="Transaction Type"
)

# Display the area chart
st.subheader("Cumulative Spending vs. Receiving Over Time")

st.plotly_chart(fig)
		

# Extract time components
categorized_transactions['Completion Time'] = pd.to_datetime(categorized_transactions['Completion Time'], errors='coerce')
categorized_transactions = categorized_transactions.sort_values(by='Completion Time')
categorized_transactions['Month'] = categorized_transactions['Completion Time'].dt.to_period('M').astype(str)
categorized_transactions['Year'] = categorized_transactions['Completion Time'].dt.to_period('Y').astype(str)

# Add a dropdown to let the user select the time period
time_period = st.selectbox(
    "Select Time Period",
    ("Monthly", "Yearly"),
    index=0  # Default is Monthly
)

# Group by category and time period
def group_transactions_by_time(df, time_period):
    if time_period == "Monthly":
        return df.groupby(['Category', 'Month'])['Paid In'].sum().unstack().fillna(0)
    elif time_period == "Yearly":
        return df.groupby(['Category', 'Year'])['Paid In'].sum().unstack().fillna(0)

# Group the transactions based on the selected time period
trends_data = group_transactions_by_time(categorized_transactions, time_period)

# Create the multi-line chart
fig = go.Figure()

for category in trends_data.index:
    fig.add_trace(go.Scatter(
        x=trends_data.columns,
        y=trends_data.loc[category],
        mode='lines',
        name=category
    ))

# Update layout
fig.update_layout(
    title=f"Category Trends Over {time_period}",
    xaxis_title=time_period,
    yaxis_title="Amount",
    template="plotly_dark",
    legend_title="Category"
)

# Display the multi-line chart
st.subheader("Category Trends Analysis")

st.plotly_chart(fig)

# Extract the transaction amounts
incoming_amounts = incoming_transactions['Paid In']
outgoing_amounts = outgoing_transactions['Withdrawn'].abs()  # Convert to positive

# Create the histograms
fig = go.Figure()

# Add histogram for incoming transactions
fig.add_trace(go.Histogram(
    x=incoming_amounts,
    name='Incoming Transactions',
    marker_color='blue',
    opacity=0.75
))

# Add histogram for outgoing transactions
fig.add_trace(go.Histogram(
    x=outgoing_amounts,
    name='Outgoing Transactions',
    marker_color='red',
    opacity=0.75
))

# Update layout
fig.update_layout(
    title="Transaction Amount Distribution",
    xaxis_title="Amount",
    yaxis_title="Frequency",
    template="plotly_dark",
    legend_title="Transaction Type",
    barmode='overlay'  # Overlay the histograms for better comparison
)

# Display the histogram
st.subheader("Transaction Amount Distribution")

st.plotly_chart(fig)
		
# Filter for savings deposits and withdrawals
savings_deposits = categorized_transactions[categorized_transactions['Category'] == "M-Shwari Deposit"]
savings_withdrawals = categorized_transactions[categorized_transactions['Category'] == "M-Shwari Withdrawal"]

# Ensure deposit amounts are positive
savings_deposits['Withdrawn'] = savings_deposits['Withdrawn'].abs()


# Create the line chart
fig = go.Figure()

# Add line for withdrawn
fig.add_trace(go.Scatter(
    x=savings_withdrawals['Completion Time'],
    y=savings_withdrawals['Paid In'],
    mode='lines',
    name='Withdrawals',
    line=dict(color='red')
))

# Add line for deposits
fig.add_trace(go.Scatter(
    x=savings_deposits['Completion Time'],
    y=savings_deposits['Withdrawn'],
    mode='lines',
    name='Deposits',
    line=dict(color='blue')
))

# Update layout
fig.update_layout(
    title="Savings Trends: Deposits vs. Withdrawals",
    xaxis_title="Date",
    yaxis_title="Amount",
    template="plotly_dark",
    legend_title="Transaction Type"
)

# Display the line chart
st.subheader("Savings Trends Analysis")

st.plotly_chart(fig)


# Count the number of transactions in each category
transaction_counts = categorized_transactions['Category'].value_counts().reset_index()
transaction_counts.columns = ['Category', 'Count']

# Create the horizontal bar chart
fig = go.Figure()

fig.add_trace(go.Bar(
    y=transaction_counts['Category'],
    x=transaction_counts['Count'],
    orientation='h',
    marker_color='blue'
))

# Update layout
fig.update_layout(
    title="Transaction Count by Category",
    xaxis_title="Number of Transactions",
    yaxis_title="Category",
    template="plotly_dark",
    legend_title="Transaction Type"
)

# Display the horizontal bar chart
st.subheader("Transaction Count by Category")

st.plotly_chart(fig)

# Define the keywords for customer transfers
transfer_keywords = ["Customer Transfer to -", "Funds received from -"]

# Apply the extraction function to the Details column for outgoing transactions
outgoing_transactions['Recipient'] = outgoing_transactions['Details'].apply(extract_name)

# Filter customer transfers
customer_transfers = outgoing_transactions[outgoing_transactions['Details'].str.contains('|'.join(transfer_keywords), case=False, na=False)]

# Calculate the average transaction amount for each recipient
average_transaction_amounts = customer_transfers.groupby('Recipient')['Withdrawn'].mean().abs().reset_index()
average_transaction_amounts = average_transaction_amounts.sort_values(by='Withdrawn', ascending=False).head(10)

# Create the bar chart
fig = go.Figure()

fig.add_trace(go.Bar(
    x=average_transaction_amounts['Withdrawn'],
    y=average_transaction_amounts['Recipient'],
    orientation='h',
    marker_color='blue'
))

# Update layout
fig.update_layout(
    title="Average Transaction Amount by Recipient",
    xaxis_title="Average Transaction Amount",
    yaxis_title="Recipient",
    template="plotly_dark",
    legend_title="Transaction Type"
)

# Display the bar chart
st.subheader("Customer Behavior Analysis: Average Transaction Amount by Recipient")

st.plotly_chart(fig)



# Identify frequent transactions
frequent_recipients = (
    outgoing_transactions_filtered['Recipient']
    .value_counts()
    .reset_index()
    .rename(columns={"index": "Recipient", "Recipient": "Count"})
    .sort_values(by="Count", ascending=False)
    .head(10)
)

frequent_senders = (
    incoming_transactions_filtered['Sender']
    .value_counts()
    .reset_index()
    .rename(columns={"index": "Sender", "Sender": "Count"})
    .sort_values(by="Count", ascending=False)
    .head(10)
)



# Display the results in the Streamlit app
st.subheader("Anomaly Detection")


col3, col4 = st.columns(2)

with col3:
    st.write("#### Top 10 Frequent Senders")
    st.dataframe(frequent_senders)

with col4:
    st.write("#### Top 10 Frequent Recipients")
    st.dataframe(frequent_recipients)


# Scatter plots for visualizing transactions
# fig_incoming_scatter = px.scatter(
#     incoming_transactions,
#     x='Completion Time',
#     y='Paid In',
#     title='Incoming Transactions',
#     hover_data=['Details']
# )

# fig_outgoing_scatter = px.scatter(
#     outgoing_transactions,
#     x='Completion Time',
#     y='Withdrawn',
#     title='Outgoing Transactions',
#     hover_data=['Details'],
#     color_discrete_sequence=['red'] 
# )

# col7, col8 = st.columns(2)

# with col7:
  
#     st.plotly_chart(fig_incoming_scatter)

# with col8:
   
#     st.plotly_chart(fig_outgoing_scatter)


# col9, col10 = st.columns(2)


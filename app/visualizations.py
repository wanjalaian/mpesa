import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

class TransactionVisualizer:
    @staticmethod
    def spending_by_category(df):
        """Create a pie chart of spending by category"""
        category_spending = df[df['Withdrawn'] < 0].groupby('category')['Withdrawn'].sum().abs()
        return px.pie(
            values=category_spending.values, 
            names=category_spending.index, 
            title='Spending Distribution by Category'
        )
    
    @staticmethod
    def monthly_cash_flow(df):
        """Create a line chart showing monthly income and expenses"""
        df['Date'] = pd.to_datetime(df['Completion Time'])
        df['Month'] = df['Date'].dt.to_period('M')
        
        monthly_income = df[df['Paid In'] > 0].groupby('Month')['Paid In'].sum()
        monthly_expenses = df[df['Withdrawn'] < 0].groupby('Month')['Withdrawn'].sum().abs()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_income.index.astype(str), 
            y=monthly_income.values, 
            mode='lines+markers', 
            name='Income'
        ))
        fig.add_trace(go.Scatter(
            x=monthly_expenses.index.astype(str), 
            y=monthly_expenses.values, 
            mode='lines+markers', 
            name='Expenses'
        ))
        
        fig.update_layout(
            title='Monthly Cash Flow',
            xaxis_title='Month',
            yaxis_title='Amount (KES)'
        )
        
        return fig
    
    @staticmethod
    def top_merchants(df, top_n=10):
        """Identify and visualize top merchants by spending"""
        merchant_spending = df[df['Withdrawn'] < 0].groupby('Details')['Withdrawn'].sum().abs()
        top_merchants = merchant_spending.nlargest(top_n)
        
        return px.bar(
            x=top_merchants.index, 
            y=top_merchants.values, 
            title=f'Top {top_n} Merchants by Spending',
            labels={'x': 'Merchant', 'y': 'Total Spending (KES)'}
        )
    
    @staticmethod
    def transaction_frequency_heatmap(df):
        """Create a heatmap of transaction frequency by day and hour"""
        df['Date'] = pd.to_datetime(df['Completion Time'])
        df['Day'] = df['Date'].dt.day_name()
        df['Hour'] = df['Date'].dt.hour
        
        transaction_heatmap = df.groupby(['Day', 'Hour']).size().unstack()
        
        return px.density_heatmap(
            z=transaction_heatmap.values,
            x=transaction_heatmap.columns,
            y=transaction_heatmap.index,
            title='Transaction Frequency Heatmap'
        )
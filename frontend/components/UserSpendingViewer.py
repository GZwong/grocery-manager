# Third-Party Imports
import pandas as pd
import plotly.express as px
import streamlit as st

# Project-Specific Imports
from frontend.api_client import get_user_spending


class UserSpendingViewer():
    
    def __init__(self, user_id: int):
        self._user_id = user_id
        
        data_exists = self._fetch_user_spending_data()
        if data_exists:
            self._process_user_spending_data()
            self._render_chart()
    
    def _fetch_user_spending_data(self):
        
        user_spending = get_user_spending(self._user_id)
        if user_spending:
            self._user_spending = user_spending
            return True
            
    def _process_user_spending_data(self):
        self._df = pd.DataFrame(self._user_spending)
    
    def _render_chart(self):
        
        self._fig = px.line(self._df, 
                            x='slot_time', 
                            y='cost', 
                            markers=True,
                            labels={
                                "slot_time": "Time",
                                "cost": "Cost [£]"
                            },
                            title="Your Spending"
                            )
        
        st.plotly_chart(self._fig, use_container_width=True)

        return self._fig
        

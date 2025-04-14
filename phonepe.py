import os
import git
import json
import pymysql
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
def get_connection():
    connection=pymysql.connect(
            host="localhost",
            user="root",
            password="Srym@1819",
            database="phonepe_1"
            )
    return connection
#cursorObject=connection.cursor()
st.set_page_config(
#page_title=("phonepe data visualization ")
page_title="PhonePe Data Visualization",
    page_icon="📊",
    layout="wide")
st.title("Phonepe pulse")
selected = option_menu(
    menu_title= "new option menu",  # Leave blank if not needed
    options=["Geo Visualization", "Top Ten Transaction", "Type of Transactions","Insights"],
    icons=["house", "code-slash", "envelope"],  # Optional
    menu_icon="cast",  # Optional
    default_index=0,
    orientation="horizontal"
)
# ✅ Fetch Available Years & Quarters
def get_years_and_quarters():
    conn = get_connection()
    query = "SELECT DISTINCT year FROM map_users ORDER BY year;"
    yearsdf = pd.read_sql(query, conn)
    years=yearsdf["year"].to_list()
    quarters = [1, 2,3, 4]  # Standard quarters
    conn.close()
    return years, quarters

# ✅ Fetch User Data Based on Selection
def get_user_data(year, quarter):
    conn = get_connection()
    query = f"""
        SELECT state, SUM(register_user) AS total_registered_users, SUM(apps_open) AS total_apps_open
        FROM map_users  
        WHERE year <= {year} AND quarter <= {quarter}
        GROUP BY state;
    """
    df = pd.read_sql(query, conn)
    #conn.close()
    return df
    # ✅ Convert State Names to Title Case to Match GeoJSO

# ✅ Fetch Transaction Data Based on Selection
def get_transaction_data(year, quarter):
    conn = get_connection()
    query = f"""
        SELECT state, 
               SUM(transaction_count) AS total_transactions, 
               SUM(transaction_amount) AS total_transaction_amount,
               AVG(transaction_amount) AS avg_transaction
        FROM agg_transaction  
        WHERE year = {year} AND quarter = {quarter}
        GROUP BY state;
    """
    df = pd.read_sql(query, conn)
    #conn.close()
    return df  
def  district_tran():  
    conn = get_connection()
     #   return pd.DataFrame()
    query="select district,sum(total_amount) as total_Amount from top_tran_districts group by district"
    df=pd.DataFrame(pd.read_sql(query,conn))
    df1=df.sort_values(by="total_Amount",ascending=False).head(10)
    return df1
def  pincode_tran():  
    conn = get_connection()
     #   return pd.DataFrame()
    query="select pincode,sum(total_amount) as total_Amount  from top_tran_pincode group by pincode"
    df_pin=pd.DataFrame(pd.read_sql(query,conn))
    df1_pin=df_pin.sort_values(by="total_Amount",ascending=False).head(10)
    return df1_pin
def state_tran():  
    conn = get_connection()
     #   return pd.DataFrame()
    query="select state,sum(transaction_amount)as total_amount from agg_transaction group by state"
    df=pd.DataFrame(pd.read_sql(query,conn))
    df1=df.sort_values(by="total_amount",ascending=False).head(10)
    return df1
def type_trans(state):
    conn = get_connection()
    query=f"""select transaction_type,sum(transaction_count) as total_count,sum(transaction_amount) as total_amount 
    from agg_transaction where state='{state}' group by transaction_type"""
    df=pd.DataFrame(pd.read_sql(query,conn))
    return df

df_states=state_tran()
state_list = df_states["state"].unique().tolist()
state_list.insert(0, "Select") 
def get_year_list():
    conn = get_connection()
    query = "select distinct year from agg_transaction"
    df_years = pd.DataFrame(pd.read_sql(query, conn))
    year_list = df_years["year"].unique().tolist()
    year_list.insert(0, "Select")
    return year_list
def insight_1(year):
    conn = get_connection()

    query1=f"""select state,sum(transaction_count) as total_tran_count from agg_transaction 
    where year={year} group by state """
    df=pd.DataFrame(pd.read_sql(query1,conn))
    return df
def insight_all_years():
    conn = get_connection()
    query = """
        SELECT state, year, SUM(transaction_amount) AS total_tran_amount
        FROM agg_transaction
        GROUP BY state, year
        ORDER BY state, year
    """
    df = pd.read_sql(query, conn)
    #conn.close()
    return df
def rank_quarter():
    conn = get_connection()
    query="""SELECT year, quarter, total_amount
    FROM (
        SELECT year, quarter, SUM(transaction_amount) AS total_amount,
            RANK() OVER (PARTITION BY year ORDER BY SUM(transaction_amount) DESC) AS rnk
        FROM agg_transaction
        GROUP BY year, quarter
    ) ranked
    WHERE rnk = 1
    ORDER BY year;"""
    df = pd.read_sql(query, conn)
    return df
if selected=="Geo Visualization":
    geo_json="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    query="""select state,sum(transaction_count) as total_tran_count,sum(transaction_amount) as total_transaction_amount,avg(transaction_amount) as avg_transaction 
    from agg_transaction group by state"""


    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()  # Get all rows
    category = st.selectbox("Select Data Type", ["Select", "User", "Transaction"])

    # 🎯 **User Must Select Year & Quarter**
    years, quarters = get_years_and_quarters()
    selected_year = st.selectbox("Select Year", ["Select"] + years, index=0)
    selected_quarter = st.selectbox("Select Quarter", ["Select"] + quarters, index=0)

    # ✅ **Check if All Selections Are Made**
    if category == "User" and selected_year != "Select" and selected_quarter != "Select":
        df = get_user_data(selected_year, selected_quarter)

        #if df.empty:
            #st.warning("⚠️ No data available for this selection!")
        #else:
            #st.dataframe(df)  # ✅ Show Data in Table

            # ✅ **Create GeoJSON Map**
        fig = px.choropleth(
            df,
            geojson=geo_json,
            featureidkey="properties.ST_NM",
            locations="state",
            color="total_registered_users",
            hover_data=["total_registered_users", "total_apps_open"],
            color_continuous_scale="Blues",
            title=f"📍 State-wise Registered Users in {selected_year} - {selected_quarter}",
        )

        fig.update_geos(fitbounds="locations", visible=False)

        # ✅ Show the Map
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("📌 **Please select 'User', Year, and Quarter to view the map.**")


    # Convert to DataFrame78++

    if category == "Transaction" and selected_year != "Select" and selected_quarter != "Select":
        df = get_transaction_data(selected_year, selected_quarter)  # ✅ Fetch transaction data

        if df is None or df.empty:
            st.warning("⚠️ No data available for this selection!")
        else:
    #df = pd.DataFrame(rows, columns=[col[0] for col in cursor.description])
    #st.dataframe(df)
    #st.dataframe(df)

    # **📍 Geo Visualization: Choropleth Map**
            fig = px.choropleth(
            df,
            geojson=geo_json,
            featureidkey="properties.ST_NM",  # Ensure this matches column names
            locations="state",
            color="total_transaction_amount",
            hover_data=["total_transactions", "avg_transaction"],
            color_continuous_scale="YlOrRd",
            title="State-wise Transaction Value",
            )

            fig.update_geos(fitbounds="locations", visible=False)


            # Show the Map
            st.plotly_chart(fig, use_container_width=True)
            #st.set_page_config
elif selected=="Top Ten Transaction":
    select_transaction=st.sidebar.selectbox("select an option",["pincode","district","state"])
    if select_transaction=="state":
        df=state_tran()
        #st.dataframe(df)
        fig, ax = plt.subplots(figsize=(10, 6))  # Set the figure size

        # Bar chart
        ax.bar(df['state'], df['total_amount'], color='skyblue')

        # Labels and title
        ax.set_xlabel("State")
        ax.set_ylabel("Total Transaction Amount")
        ax.set_title("Top 10 States with Highest Transactions")
        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

        st.pyplot(fig)  # Display in Streamlit
    elif select_transaction=="district":
        df=district_tran()
        
        st.subheader("📌 Top 10 district with Highest Transactions")
        #st.dataframe(df)
        fig = px.bar(df, x="district", y="total_Amount", color="total_Amount",
                    title="Top 10 state with Highest Transactions", labels={"total_transaction_amount": "Transaction Amount"})
        st.plotly_chart(fig, use_container_width=True)
    elif select_transaction=="pincode":
        df=pincode_tran()
        
        st.subheader("📌 Top 10 pincode with Highest Transactions")
        #st.dataframe(df)
        #fig = px.bar(df, x="pincode", y="total_Amount", color="total_Amount",
                   # title="Top 10 state with Highest Transactions", labels={"total_transaction_amount": "Transaction Amount"})
        fig=px.pie(df, names='pincode',
        values='total_Amount', # or 'total_count' if you prefer
        
        color_discrete_sequence=px.colors.qualitative.Set2)

        st.plotly_chart(fig, use_container_width=True)
elif selected=="Type of Transactions":
    select_state=st.sidebar.selectbox("select state",state_list )
    if select_state!="select":
        df=type_trans(select_state)
        fig = px.bar(
                df,
                x="transaction_type",
                y="total_amount",
                text="total_amount",
                color="transaction_type",
                title=f"Transaction Amount by Type - {select_state}"
            )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("👈 Please select a state from the sidebar to view details.")
elif selected=="Insights":
    year_list=get_year_list()
    select_year=st.sidebar.selectbox("select year",year_list )
    if select_year!="Select":
        df=insight_1(select_year)
        fig = px.bar(
        df,
        x='state',
        y='total_tran_count',
        color='total_tran_count',
        
        title=f'Aggregated Transactions Over Time{select_year}')
        fig.update_layout(
                xaxis_title='State',
                yaxis_title='Total Transaction Count',
                coloraxis_colorbar=dict(title="Transactions"),
                xaxis_tickangle=45
            )

        st.plotly_chart(fig)
    df = insight_all_years()

# Pivot for heatmap
    pivot_df = df.pivot(index="state", columns="year", values="total_tran_amount")

    fig = px.imshow(
        pivot_df,
        text_auto=True,
        color_continuous_scale='Blues',
        title="Heatmap of Transaction Counts by State and Year"
    )

    st.plotly_chart(fig)

    top_quarter=rank_quarter()
    fig = px.bar(
    top_quarter,
    x='year',
    y='total_amount',
    color='quarter',          # Color bars by quarter
    text='quarter',           # Display the quarter on top of bars
    title='Top Performing Quarter by Transaction Amount (Year-wise)'
    )

    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Transaction Amount',
        showlegend=True,
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    st.plotly_chart(fig)


    


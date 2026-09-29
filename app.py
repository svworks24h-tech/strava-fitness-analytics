import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="Bellabeat Fitness Analytics", page_icon="💚", layout="wide")

BASE = Path(__file__).parent
DATA = BASE / "data"
DB = DATA / "bellabeat.db"

@st.cache_data
def load_data():
    activity = pd.read_csv(DATA / "FactActivity.csv", parse_dates=["activity_date"])
    sleep = pd.read_csv(DATA / "FactSleep.csv", parse_dates=["sleep_date"])
    return activity, sleep

@st.cache_data
def run_sql(query):
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query(query, conn)

activity, sleep = load_data()

st.sidebar.title("Bellabeat Analytics")
page = st.sidebar.radio(
    "Navigate",
    ["Executive Dashboard", "Activity Analysis", "Sleep Analysis", "SQL Analysis", "Insights & Recommendations"]
)

# ---------------- EXECUTIVE ----------------
if page == "Executive Dashboard":
    st.title("💚 Bellabeat Fitness Analytics Dashboard")
    st.caption("Smart-device activity and sleep behavior analysis")

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Users", activity["user_id"].nunique())
    c2.metric("Avg Daily Steps", f'{activity["totalsteps"].mean():,.0f}')
    c3.metric("Avg Daily calories", f'{activity["calories"].mean():,.0f}')
    c4.metric("Avg Active Minutes", f'{activity["active_minutes"].mean():,.0f}')
    c5.metric("Avg Sleep Hours", f'{sleep["total_minutes_asleep"].mean()/60:.1f}')

    st.subheader("Daily Activity Trend")
    daily = activity.groupby("activity_date", as_index=False).agg(
        Average_Steps=("totalsteps","mean"),
        Average_calories=("calories","mean")
    )
    fig = px.line(daily, x="activity_date", y="Average_Steps",
                  markers=True, title="Average Daily Steps")
    st.plotly_chart(fig, use_container_width=True)

    col1,col2 = st.columns(2)
    with col1:
        weekday = activity.copy()
        weekday["Day"] = weekday["activity_date"].dt.day_name()
        order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        wd=weekday.groupby("Day",as_index=False)["totalsteps"].mean()
        wd["Day"]=pd.Categorical(wd["Day"],categories=order,ordered=True)
        wd=wd.sort_values("Day")
        fig=px.bar(wd,x="Day",y="totalsteps",title="Average Steps by Day")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig=px.scatter(activity,x="totalsteps",y="calories",
                       title="Steps vs calories",
                       opacity=0.65)
        st.plotly_chart(fig,use_container_width=True)

# ---------------- ACTIVITY ----------------
elif page == "Activity Analysis":
    st.title("🏃 Activity Analysis")

    col1,col2,col3,col4=st.columns(4)
    col1.metric("Avg Steps",f'{activity["totalsteps"].mean():,.0f}')
    col2.metric("Avg Active Minutes",f'{activity["active_minutes"].mean():,.0f}')
    col3.metric("Avg Sedentary Minutes",f'{activity["sedentaryminutes"].mean():,.0f}')
    col4.metric("Avg Active Distance",f'{activity["active_distance"].mean():.2f}')

    fig=px.histogram(activity,x="totalsteps",nbins=30,title="Distribution of Daily Steps")
    st.plotly_chart(fig,use_container_width=True)

    col1,col2=st.columns(2)
    with col1:
        intensity=pd.DataFrame({
            "Intensity":["Very Active","Fairly Active","Lightly Active","Sedentary"],
            "Minutes":[
                activity["veryactiveminutes"].mean(),
                activity["fairlyactiveminutes"].mean(),
                activity["lightlyactiveminutes"].mean(),
                activity["sedentaryminutes"].mean()
            ]
        })
        fig=px.bar(intensity,x="Intensity",y="Minutes",title="Average Minutes by Activity Level")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig=px.scatter(activity,x="totalsteps",y="calories",
                       size="active_minutes",title="Steps, calories & Active Minutes",
                       hover_data=["user_id","activity_date"])
        st.plotly_chart(fig,use_container_width=True)

# ---------------- SLEEP ----------------
elif page == "Sleep Analysis":
    st.title("😴 Sleep Analysis")

    col1,col2,col3=st.columns(3)
    col1.metric("Sleep Users",sleep["user_id"].nunique())
    col2.metric("Avg Sleep",f'{sleep["total_minutes_asleep"].mean()/60:.1f} hrs')
    col3.metric("Avg Time in Bed",f'{sleep["total_time_in_bed"].mean()/60:.1f} hrs')

    sleep_plot=sleep.copy()
    sleep_plot["Sleep Hours"]=sleep_plot["total_minutes_asleep"]/60
    fig=px.histogram(sleep_plot,x="Sleep Hours",nbins=25,title="Distribution of Sleep Duration")
    st.plotly_chart(fig,use_container_width=True)

    merged=activity.merge(
        sleep[["user_id","sleep_date","total_minutes_asleep","total_time_in_bed"]],
        left_on=["user_id","activity_date"],
        right_on=["user_id","sleep_date"],
        how="inner"
    )
    merged["Sleep Hours"]=merged["total_minutes_asleep"]/60

    col1,col2=st.columns(2)
    with col1:
        fig=px.scatter(merged,x="Sleep Hours",y="totalsteps",
                       title="Sleep vs Steps",opacity=0.7)
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig=px.scatter(merged,x="Sleep Hours",y="active_minutes",
                       title="Sleep vs Active Minutes",opacity=0.7)
        st.plotly_chart(fig,use_container_width=True)

# ---------------- SQL ----------------
elif page == "SQL Analysis":
    st.title("🗄️ SQL Analysis")
    st.write("The queries below execute against the local SQLite database created from the validated cleaned datasets.")

    queries = {
        "1. User Activity Summary": """
SELECT user_id,
       COUNT(*) AS activity_days,
       ROUND(AVG(totalsteps), 0) AS avg_steps,
       ROUND(AVG(calories), 0) AS avg_calories,
       ROUND(AVG(active_minutes), 0) AS avg_active_minutes
FROM FactActivity
GROUP BY user_id
ORDER BY avg_steps DESC;
""",
        "2. Activity by Weekday": """
SELECT day_of_week,
       COUNT(*) AS records,
       ROUND(AVG(totalsteps), 0) AS avg_steps,
       ROUND(AVG(calories), 0) AS avg_calories
FROM FactActivity
GROUP BY day_number, day_of_week
ORDER BY day_number;
""",
        "3. Most Sedentary Days": """
SELECT activity_date,
       ROUND(AVG(sedentaryminutes), 0) AS avg_sedentary_minutes
FROM FactActivity
GROUP BY activity_date
ORDER BY avg_sedentary_minutes DESC
LIMIT 10;
""",
        "4. Sleep Summary": """
SELECT ROUND(AVG(total_minutes_asleep), 1) AS avg_sleep_minutes,
       ROUND(AVG(total_time_in_bed), 1) AS avg_time_in_bed_minutes,
       COUNT(DISTINCT user_id) AS sleep_users
FROM FactSleep;
""",
        "5. Activity + Sleep": """
SELECT a.user_id,
       a.activity_date,
       a.totalsteps,
       a.active_minutes,
       s.total_minutes_asleep
FROM FactActivity a
JOIN FactSleep s
  ON a.user_id = s.user_id
 AND a.activity_date = s.sleep_date
ORDER BY a.activity_date, a.user_id;
"""
    }

    selected=st.selectbox("Choose SQL analysis",list(queries.keys()))
    query=queries[selected]
    st.code(query,language="sql")
    result=run_sql(query)
    st.dataframe(result,use_container_width=True)
    st.caption(f"Rows returned: {len(result):,}")

# ---------------- INSIGHTS ----------------
else:
    st.title("💡 Insights & Recommendations")
    st.subheader("Key analytical observations")

    avg_steps=activity["totalsteps"].mean()
    avg_sleep=sleep["total_minutes_asleep"].mean()/60
    avg_sedentary=activity["sedentaryminutes"].mean()

    st.markdown(f"""
- Average daily steps across activity records: **{avg_steps:,.0f}**.
- Average sleep duration across sleep records: **{avg_sleep:.1f} hours**.
- Average sedentary time across activity records: **{avg_sedentary:,.0f} minutes**.
- The dataset contains activity and sleep observations from different numbers of users, so comparisons should account for coverage.
""")

    st.subheader("Marketing / product implications")
    st.markdown("""
1. Use activity tracking to encourage consistent daily movement.
2. Use sleep insights as a complementary wellness-engagement feature.
3. Use personalized reminders or challenges based on observed activity patterns.
4. Segment messaging by behavior rather than treating every user identically.
5. Continue collecting broader and more consistent user data to strengthen future analysis.

**Important:** These are analytical implications, not causal conclusions. The dataset shows associations and behavioral patterns; it does not establish that one behavior causes another.
""")

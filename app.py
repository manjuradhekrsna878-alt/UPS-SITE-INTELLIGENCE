
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import sqlite3, os

DB = "ups_sites.db"

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_name TEXT, client TEXT, facility TEXT, location TEXT,
        distance_km REAL, travel_min REAL, status TEXT,
        contact_name TEXT, designation TEXT, phone TEXT, email TEXT,
        oem TEXT, model TEXT, capacity_kva REAL, capacity_kw REAL,
        qty INTEGER, configuration TEXT, technology TEXT,
        battery_oem TEXT, battery_model TEXT, battery_type TEXT,
        battery_ah REAL, blocks_per_string INTEGER, strings INTEGER,
        battery_install_year INTEGER, battery_condition TEXT,
        load_kw REAL, load_kva REAL, pf REAL, load_pct REAL,
        peak_kw REAL, min_kw REAL, avg_kw REAL, step_kw REAL,
        opportunity TEXT, notes TEXT, next_followup TEXT
    )""")
    con.commit()
    return con

def save_site(data):
    con = sqlite3.connect(DB)
    cols = ",".join(data.keys())
    vals = list(data.values())
    placeholders = ",".join(["?"]*len(vals))
    con.execute(f"INSERT INTO sites ({cols}) VALUES ({placeholders})", vals)
    con.commit()

def load_sites():
    con = sqlite3.connect(DB)
    return pd.read_sql_query("SELECT * FROM sites ORDER BY id DESC", con)

init_db()
st.set_page_config(page_title="UPS Site Intelligence", page_icon="⚡", layout="wide")

st.title("⚡ UPS Site Intelligence")
st.caption("UPS site survey • asset intelligence • load dynamics • opportunity management")

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

pages = ["Dashboard", "New Site Survey", "Site Register", "Load Dynamics", "Opportunity Engine", "Reports"]

with st.sidebar:
    st.header("Navigation")
    for p in pages:
        if st.button(p, use_container_width=True):
            st.session_state.page = p
    st.divider()
    st.info("Prototype v1.0\nMobile-friendly Streamlit application")

df = load_sites()

if st.session_state.page == "Dashboard":
    st.subheader("Dashboard")

    # Count sites that need technical or commercial attention.
    def site_needs_action(row):
        signals = []

        if pd.notna(row["battery_install_year"]) and row["battery_install_year"] > 0:
            if date.today().year - int(row["battery_install_year"]) >= 4:
                signals.append("Battery age review")

        if str(row["battery_condition"]).strip() in ["Watch", "Poor"]:
            signals.append("Battery condition")

        if pd.notna(row["load_pct"]) and row["load_pct"] >= 75:
            signals.append("Capacity review")

        if pd.notna(row["step_kw"]) and row["step_kw"] > 0:
            signals.append("Dynamic-load review")

        opportunity = str(row["opportunity"]).strip()
        if opportunity and opportunity != "None":
            signals.append(opportunity)

        return len(signals) > 0

    action_required = int(df.apply(site_needs_action, axis=1).sum()) if len(df) else 0
    battery_sites = int(
        df["battery_model"].fillna("").astype(str).str.strip().ne("").sum()
    ) if len(df) else 0
    opportunities = int(
        df["opportunity"].fillna("").astype(str).str.strip().ne("").sum()
        - df["opportunity"].fillna("").astype(str).str.strip().eq("None").sum()
    ) if len(df) else 0
    avg_load = round(
        pd.to_numeric(df["load_pct"], errors="coerce").mean(), 1
    ) if len(df) else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Sites", len(df))
    c2.metric("Sites Requiring Action", action_required)
    c3.metric("Battery Sites", battery_sites)
    c4.metric("Opportunities", opportunities)
    c5.metric("Avg Load %", avg_load)
    st.divider()
    if len(df):
        a,b = st.columns(2)
        with a:
            st.write("**UPS OEM distribution**")
            st.bar_chart(df["oem"].fillna("Unknown").value_counts())
        with b:
            st.write("**Opportunity distribution**")
            st.bar_chart(df["opportunity"].fillna("None").value_counts())
        st.write("**Recent sites**")
        st.dataframe(df[["site_name","client","location","oem","model","capacity_kva","load_pct","opportunity","next_followup"]], use_container_width=True)
    else:
        st.info("No sites yet. Start with New Site Survey.")

elif st.session_state.page == "New Site Survey":
    st.subheader("New UPS Site Survey")
    with st.form("survey"):
        st.markdown("### 1. Site Information")
        c1,c2,c3 = st.columns(3)
        site_name = c1.text_input("Site name *")
        client = c2.text_input("Client")
        facility = c3.selectbox("Facility type", ["Data Centre","Hospital","Hotel","Bank/Finance","Industrial","Office","Telecom","Government","Other"])
        location = st.text_input("Location / address")
        c1,c2 = st.columns(2)
        distance_km = c1.number_input("Distance (km)", min_value=0.0, step=0.5)
        travel_min = c2.number_input("Travel duration (min)", min_value=0.0, step=5.0)
        status = st.selectbox("Site status", ["Surveyed","Prospect","Existing Customer","Opportunity","Closed"])

        st.markdown("### 2. Contact")
        c1,c2,c3,c4 = st.columns(4)
        contact_name = c1.text_input("Contact name")
        designation = c2.text_input("Designation")
        phone = c3.text_input("Mobile")
        email = c4.text_input("Email")

        st.markdown("### 3. UPS")
        c1,c2,c3,c4 = st.columns(4)
        oem = c1.text_input("OEM", placeholder="ABB / Vertiv / Eaton...")
        model = c2.text_input("Model")
        capacity_kva = c3.number_input("UPS capacity (kVA)", min_value=0.0, step=1.0)
        capacity_kw = c4.number_input("UPS capacity (kW)", min_value=0.0, step=1.0)
        c1,c2,c3 = st.columns(3)
        qty = c1.number_input("Quantity", min_value=1, step=1)
        configuration = c2.selectbox("Configuration", ["N","N+1","2N","2N+1","Parallel","Standalone","Unknown"])
        technology = c3.selectbox("Technology", ["Modular Online","Monoblock Online","Transformerless","Transformer-based","Unknown"])

        st.markdown("### 4. Battery")
        c1,c2,c3,c4 = st.columns(4)
        battery_oem = c1.text_input("Battery OEM")
        battery_model = c2.text_input("Battery model")
        battery_type = c3.selectbox("Battery type", ["VRLA AGM","VRLA Gel","Lithium-ion","Ni-Cd","Other","Unknown"])
        battery_ah = c4.number_input("Battery Ah", min_value=0.0, step=1.0)
        c1,c2,c3 = st.columns(3)
        blocks_per_string = c1.number_input("Blocks per string", min_value=0, step=1)
        strings = c2.number_input("Number of strings", min_value=0, step=1)
        battery_install_year = c3.number_input("Installation year", min_value=0, max_value=date.today().year, step=1)
        battery_condition = st.selectbox("Battery condition", ["Good","Watch","Poor","Unknown"])

        st.markdown("### 5. Load")
        c1,c2,c3,c4 = st.columns(4)
        load_kw = c1.number_input("Present load (kW)", min_value=0.0, step=1.0)
        load_kva = c2.number_input("Present load (kVA)", min_value=0.0, step=1.0)
        pf = c3.number_input("Power factor", min_value=0.0, max_value=1.0, value=0.9, step=0.01)
        load_pct = c4.number_input("Load (%)", min_value=0.0, max_value=100.0, step=1.0)
        c1,c2,c3 = st.columns(3)
        peak_kw = c1.number_input("Peak kW", min_value=0.0, step=1.0)
        min_kw = c2.number_input("Minimum kW", min_value=0.0, step=1.0)
        avg_kw = c3.number_input("Average kW", min_value=0.0, step=1.0)
        step_kw = st.number_input("Largest step-load change (kW)", min_value=0.0, step=1.0)

        st.markdown("### 6. Commercial Opportunity")
        opportunity = st.selectbox("Primary opportunity", ["None","Battery Replacement","UPS Replacement","Capacity Expansion","AMC","Retrofit/Modernization","Monitoring/DCIM","Multiple"])
        notes = st.text_area("Notes / observations")
        next_followup = st.date_input("Next follow-up", value=date.today()+timedelta(days=7))
        submitted = st.form_submit_button("Save Site Survey", type="primary")

        if submitted:
            if not site_name.strip():
                st.error("Site name is required.")
            else:
                save_site({
                    "site_name":site_name,"client":client,"facility":facility,"location":location,
                    "distance_km":distance_km,"travel_min":travel_min,"status":status,
                    "contact_name":contact_name,"designation":designation,"phone":phone,"email":email,
                    "oem":oem,"model":model,"capacity_kva":capacity_kva,"capacity_kw":capacity_kw,
                    "qty":qty,"configuration":configuration,"technology":technology,
                    "battery_oem":battery_oem,"battery_model":battery_model,"battery_type":battery_type,
                    "battery_ah":battery_ah,"blocks_per_string":blocks_per_string,"strings":strings,
                    "battery_install_year":battery_install_year,"battery_condition":battery_condition,
                    "load_kw":load_kw,"load_kva":load_kva,"pf":pf,"load_pct":load_pct,
                    "peak_kw":peak_kw,"min_kw":min_kw,"avg_kw":avg_kw,"step_kw":step_kw,
                    "opportunity":opportunity,"notes":notes,"next_followup":str(next_followup)
                })
                st.success("Site survey saved.")

elif st.session_state.page == "Site Register":
    st.subheader("Site Register")
    if len(df):
        search = st.text_input("Search site / client / OEM / location")
        show = df.copy()
        if search:
            mask = show.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            show = show[mask]
        st.dataframe(show, use_container_width=True, height=600)
        st.download_button("Export CSV", show.to_csv(index=False).encode(), "ups_site_register.csv", "text/csv")
    else:
        st.info("No records.")

elif st.session_state.page == "Load Dynamics":
    st.subheader("UPS Load Dynamics Study")
    st.write("Upload a CSV with columns: **Time, kW**. Optional columns: kVA, PF.")
    uploaded = st.file_uploader("Upload load profile CSV", type=["csv"])
    if uploaded:
        x = pd.read_csv(uploaded)
        if "kW" not in x.columns:
            st.error("CSV must contain a 'kW' column.")
        else:
            x["kW"] = pd.to_numeric(x["kW"], errors="coerce")
            x = x.dropna(subset=["kW"])
            avg = x.kW.mean(); peak = x.kW.max(); minimum = x.kW.min()
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Average kW", f"{avg:.1f}")
            c2.metric("Peak kW", f"{peak:.1f}")
            c3.metric("Minimum kW", f"{minimum:.1f}")
            c4.metric("Peak / Avg", f"{peak/avg:.2f}x" if avg else "—")
            st.line_chart(x.set_index("Time")["kW"] if "Time" in x.columns else x["kW"])
            if len(x) > 1:
                x["Step Change kW"] = x["kW"].diff().abs()
                st.metric("Largest step-load change", f"{x['Step Change kW'].max():.1f} kW")
            st.dataframe(x, use_container_width=True)
            st.download_button("Download analyzed CSV", x.to_csv(index=False).encode(), "load_dynamics_analysis.csv", "text/csv")
    else:
        st.info("Use the uploader to analyze a real site load profile.")

elif st.session_state.page == "Opportunity Engine":
    st.subheader("Opportunity Engine")
    if len(df):
        opp = df.copy()
        opp["Calculated signal"] = ""
        for i,r in opp.iterrows():
            signals=[]
            if pd.notna(r.battery_install_year) and r.battery_install_year > 0 and date.today().year-r.battery_install_year >= 4:
                signals.append("Battery age review")
            if str(r.battery_condition).strip() in ["Watch", "Poor"]:
                signals.append("Battery condition")
            if pd.notna(r.load_pct) and r.load_pct >= 75:
                signals.append("Capacity review")
            if pd.notna(r.step_kw) and r.step_kw > 0:
                signals.append("Dynamic-load review")
            if r.opportunity and r.opportunity != "None":
                signals.append(r.opportunity)
            opp.loc[i,"Calculated signal"]="; ".join(signals) or "Monitor"
        st.dataframe(opp[["site_name","client","oem","model","capacity_kva","load_pct","battery_install_year","battery_condition","opportunity","Calculated signal"]], use_container_width=True)
    else:
        st.info("Add sites first.")

elif st.session_state.page == "Reports":
    st.subheader("Site Report Preview")
    if len(df):
        options = df["site_name"].tolist()
        selected = st.selectbox("Select site", options)
        r = df[df.site_name==selected].iloc[0]
        st.markdown(f"## {r.site_name}")
        st.write(f"**Client:** {r.client}  |  **Facility:** {r.facility}  |  **Location:** {r.location}")
        st.write(f"**Contact:** {r.contact_name} — {r.designation} — {r.phone}")
        st.markdown("### UPS")
        st.write(f"{r.oem} {r.model} — {r.capacity_kva} kVA / {r.capacity_kw} kW — Qty {r.qty} — {r.configuration} — {r.technology}")
        st.markdown("### Battery")
        st.write(f"{r.battery_oem} {r.battery_model} — {r.battery_type} — {r.battery_ah} Ah — {r.blocks_per_string} blocks/string — {r.strings} strings — Condition: {r.battery_condition}")
        st.markdown("### Load")
        st.write(f"Present: {r.load_kw} kW / {r.load_kva} kVA | PF {r.pf} | Load {r.load_pct}% | Peak {r.peak_kw} kW | Avg {r.avg_kw} kW | Min {r.min_kw} kW | Step {r.step_kw} kW")
        st.markdown("### Commercial")
        st.write(f"**Opportunity:** {r.opportunity}")
        st.write(f"**Next follow-up:** {r.next_followup}")
        st.write(r.notes)
    else:
        st.info("No site records.")

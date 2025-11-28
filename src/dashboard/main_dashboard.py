import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import glob
import sys
import time
import yfinance as yf
from datetime import datetime, timedelta

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Macro Event Tracker",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. INSTITUTIONAL CSS ---
st.markdown("""
<style>
    /* Global Font & Background */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: #000000;
        color: #e0e0e0;
    }
    
    /* Spacing adjustments */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Metric Cards - Institutional Look */
    div[data-testid="stMetric"] {
        background-color: #121212;
        border: 1px solid #333333;
        padding: 15px;
        border-radius: 0px;
    }
    label[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #888888;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #ffffff;
        font-weight: 500;
    }
    
    /* Tables & Tabs */
    div[data-testid="stDataFrame"] { border: 1px solid #333333; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background-color: #000000; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #121212;
        border-radius: 0px;
        color: #888888;
        font-size: 0.9rem;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #333333;
        color: white;
        border-bottom: none; 
    }
    
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .section-header {
        font-size: 0.9rem;
        font-weight: 700;
        color: #666666;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA LOADING ---
data_path = "data/processed/"
all_files = glob.glob(os.path.join(data_path, "*.csv"))

# Filter out calendar
chart_files = [f for f in all_files if "calendar.csv" not in f]

# === CLOUD AUTO-FIX LOGIC ===
if not chart_files:
    with st.spinner("🚀 First-run detected: Initializing Cloud Engine & Fetching Data from FRED..."):
        try:
            # Point to root directory so we can import modules
            sys.path.append(os.getcwd())
            from src.processing.scheduler import MacroScheduler
            
            # Run one cycle to generate CSVs
            scheduler = MacroScheduler()
            scheduler.run_pipeline()
            
            time.sleep(1) # Brief pause to ensure file write
            st.rerun() # Refresh to load the new data
            
        except Exception as e:
            st.error(f"Critical Boot Error: {e}")
            st.stop()
# ============================

data_store = {}
for f in chart_files:
    try:
        name = os.path.basename(f).replace(".csv", "").replace("_", " ").upper()
        df = pd.read_csv(f)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # NFP Logic: 159 -> 159,000
        if "NFP" in name or "PAYROLL" in name:
            df['value'] = df['value'] * 1000
            
        data_store[name] = df
    except Exception:
        pass

# --- 4. MARKET DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_market_data(ticker, start_date):
    try:
        safe_start = start_date - timedelta(days=30)
        df = yf.download(ticker, start=safe_start, progress=False)
        # Handle MultiIndex if returned by newer yfinance versions
        if isinstance(df.columns, pd.MultiIndex):
            return df['Close'].iloc[:, 0]
        return df['Close']
    except Exception:
        return pd.Series()

MARKET_ASSETS = {
    "None": None,
    "S&P 500 (SPY)": "SPY",
    "US 10Y Treasury Yield": "^TNX",
    "USD Index (DXY)": "DX-Y",
    "GBP/USD": "GBPUSD=X",
    "EUR/USD": "EURUSD=X",
    "Bitcoin (BTC)": "BTC-USD"
}

# --- 5. SIDEBAR CONFIGURATION ---
if st.sidebar.button("REFRESH DATA", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Tracking {len(data_store)} Macro Indicators")
st.sidebar.caption("Source: FRED / ECB Data Portal")

# --- CUSTOM SORT ORDER ---
DISPLAY_ORDER = [
    "US CPI",
    "US PPI",
    "US NFP",
    "US UNEMPLOYMENT",
    "UK INFLATION",
    "EUROZONE INFLATION"
]

sorted_data_store = {}
for key in DISPLAY_ORDER:
    if key in data_store:
        sorted_data_store[key] = data_store[key]

# --- 6. DASHBOARD HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("### MACRO EVENT TRACKER | REAL-TIME ANALYTICS")
    st.markdown(f"<div style='color: #666; font-size: 0.8rem;'>DASHBOARD DATE: {datetime.now().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

st.markdown("---")

# --- 7. MARKET OVERVIEW (TICKER) ---
st.markdown('<div class="section-header">Most Recent Readings</div>', unsafe_allow_html=True)

cols = st.columns(len(sorted_data_store)) 

for idx, (name, df) in enumerate(sorted_data_store.items()):
    if df.empty: continue
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    val = latest['value']
    delta = val - prev['value']
    
    # Conditional Formatting
    if "NFP" in name:
        val_fmt = f"{val:,.0f}" 
    else:
        val_fmt = f"{val:,.2f}" 
        
    with cols[idx]:
        st.metric(
            label=name,
            value=val_fmt,
            delta=f"{delta:+.2f}"
        )

st.markdown("<br><br>", unsafe_allow_html=True)

# --- 8. MAIN WORKSPACE ---
tab_chart, tab_data, tab_cal = st.tabs(["ANALYTICS & CHARTING", "RAW DATA LOG", "UPCOMING CALENDAR"])

with tab_chart:
    st.markdown("##")
    col_ctrl, col_graph = st.columns([1, 4])
    
    with col_ctrl:
        st.markdown("###### INDICATOR SELECTION")
        selected_series = st.radio("Select Series", list(sorted_data_store.keys()), label_visibility="collapsed")
        
        # --- UK WARNING ---
        if selected_series == "UK INFLATION":
            st.warning("⚠️ UK Data sourced via FRED. Cross-reference with ONS for live trading.")
        
        st.markdown("---")
        
        st.markdown("###### MARKET OVERLAY")
        selected_market = st.selectbox("Compare vs Asset:", list(MARKET_ASSETS.keys()), index=0)
        
        st.markdown("---")
        
        df_chart = sorted_data_store[selected_series]
        
        # 12M Stats Logic
        latest_date = df_chart['date'].max()
        cutoff_date = latest_date - pd.DateOffset(years=1)
        stats_df = df_chart[df_chart['date'] > cutoff_date]
        
        if not stats_df.empty:
            current_vol = stats_df['value'].std()
            high_12m = stats_df['value'].max()
            low_12m = stats_df['value'].min()
        else:
            current_vol = df_chart['value'].std()
            high_12m = df_chart['value'].max()
            low_12m = df_chart['value'].min()
        
        st.markdown(f"""
        <div style='background-color: #121212; padding: 10px; border: 1px solid #333;'>
            <div style='color: #888; font-size: 0.75rem;'>12M VOLATILITY (SD)</div>
            <div style='color: #fff; font-size: 1.1rem; margin-bottom: 8px;'>{current_vol:,.2f}</div>
            <div style='color: #888; font-size: 0.75rem;'>12M HIGH</div>
            <div style='color: #fff; font-size: 1.1rem; margin-bottom: 8px;'>{high_12m:,.2f}</div>
            <div style='color: #888; font-size: 0.75rem;'>12M LOW</div>
            <div style='color: #fff; font-size: 1.1rem;'>{low_12m:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_graph:
        st.caption("ℹ️ **Smart View:** Default restricted to last 10 years with outlier clipping. Use mouse wheel to zoom, click-drag to pan.")
        
        max_date_ts = df_chart['date'].max()
        min_date_ts = max_date_ts - pd.DateOffset(years=10)
        
        # Smart Scaling Calculation
        y_lower = df_chart['value'].quantile(0.01)
        y_upper = df_chart['value'].quantile(0.99)
        y_buffer = (y_upper - y_lower) * 0.1 if y_upper != y_lower else 1.0
        final_y_min = y_lower - y_buffer
        final_y_max = y_upper + y_buffer
        
        fig = go.Figure()
        
        # 1. PRIMARY MACRO DATA (Right Axis)
        fig.add_trace(go.Scatter(
            x=df_chart['date'], y=df_chart['value'],
            mode='lines', name='Actual',
            line=dict(color='#00E396', width=2), 
            fill='tozeroy', fillcolor='rgba(0, 227, 150, 0.1)' 
        ))
        
        df_chart['MA'] = df_chart['value'].rolling(window=12).mean()
        fig.add_trace(go.Scatter(
            x=df_chart['date'], y=df_chart['MA'],
            mode='lines', name='12M Trend',
            line=dict(color='#FF8C00', width=1)
        ))

        # 2. MARKET DATA (Left Axis)
        if selected_market != "None":
            ticker = MARKET_ASSETS[selected_market]
            market_data = fetch_market_data(ticker, min_date_ts)
            
            if not market_data.empty:
                fig.add_trace(go.Scatter(
                    x=market_data.index,
                    y=market_data.values,
                    mode='lines',
                    name=selected_market,
                    yaxis="y2", 
                    line=dict(color='#90A4AE', width=1.5), # Professional Silver
                    opacity=0.8
                ))

        fig.update_layout(
            height=550,
            paper_bgcolor="#000000", plot_bgcolor="#000000",
            # Increased bottom margin to fit the legend comfortably
            margin=dict(l=60, r=60, t=30, b=50),
            dragmode='pan', 
            
            xaxis=dict(
                title=dict(text="DATE", font=dict(color="#cccccc", size=12)),
                showgrid=False, linecolor='#333', tickfont=dict(color='#666'),
                range=[min_date_ts, max_date_ts],
                
                # Range Selector
                rangeslider=dict(visible=True, bordercolor="#333", borderwidth=1, bgcolor="#121212"),
                rangeselector=dict(
                    buttons=list([
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(count=5, label="5Y", step="year", stepmode="backward"),
                        dict(step="all", label="MAX")
                    ]),
                    bgcolor="#121212", activecolor="#333", font=dict(color="white")
                ),
                
                fixedrange=False,
                tickformat="%d/%m/%Y"
            ),
            
            # RIGHT AXIS (Macro Data - DYNAMIC TITLE)
            yaxis=dict(
                title=dict(text=selected_series, font=dict(color="#00E396", size=12, weight="bold")),
                showgrid=True, gridcolor='#222', zeroline=False, side='right', 
                tickfont=dict(color='#00E396'),
                range=[final_y_min, final_y_max], autorange=False, fixedrange=False
            ),
            
            # LEFT AXIS (Market Overlay - DYNAMIC TITLE)
            yaxis2=dict(
                title=dict(text=selected_market if selected_market != "None" else "", font=dict(color="#90A4AE", size=12, weight="bold")),
                overlaying="y", side="left", showgrid=False,
                tickfont=dict(color='#90A4AE'),
                fixedrange=False,
                # tickformat removed to allow auto-precision (fixing the EUR/USD issue)
            ),
            
            hovermode="x unified", 
            showlegend=True,
            
            # MOVED LEGEND TO BOTTOM CENTER
            legend=dict(
                orientation="h", 
                y=-0.2, # Push below the axis
                x=0.5, 
                xanchor="center", 
                bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ccc")
            )
        )
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

with tab_data:
    st.markdown("##")
    master_log = pd.DataFrame()
    for name, df in sorted_data_store.items():
        temp = df.copy()
        temp['indicator'] = name
        master_log = pd.concat([master_log, temp])
    
    all_indicators = DISPLAY_ORDER
    c_filter, _ = st.columns([1, 2])
    with c_filter:
        selected_indicators = st.multiselect("Filter by Indicator ID:", options=all_indicators, default=all_indicators)
    
    if selected_indicators:
        filtered_log = master_log[master_log['indicator'].isin(selected_indicators)]
    else:
        filtered_log = master_log
        
    filtered_log = filtered_log.sort_values(by=['date', 'indicator'], ascending=[False, True])
    
    # Left Alignment Logic
    def format_for_display(row):
        val = row['value']
        if "NFP" in row['indicator']:
            return f"{val:,.0f}" 
        else:
            return f"{val:,.2f}"

    display_df = filtered_log.copy()
    display_df['Actual Value'] = display_df.apply(format_for_display, axis=1)
    
    st.dataframe(
        display_df,
        column_config={
            "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "Actual Value": st.column_config.TextColumn("Actual"),
            "indicator": "Indicator ID",
            "source": "Source"
        },
        column_order=["date", "indicator", "Actual Value", "source"],
        use_container_width=True,
        height=600,
        hide_index=True
    )

with tab_cal:
    st.markdown("##")
    try:
        cal_path = os.path.join(data_path, "calendar.csv")
        cal_df = pd.read_csv(cal_path)
        
        all_cal_indicators = sorted(cal_df['Indicator'].unique())
        c_cal_filter, _ = st.columns([1, 2])
        with c_cal_filter:
            selected_cal = st.multiselect("Filter Calendar:", options=all_cal_indicators, default=all_cal_indicators)
            
        if selected_cal:
            cal_df = cal_df[cal_df['Indicator'].isin(selected_cal)]
            
        st.dataframe(
            cal_df,
            column_config={
                "Indicator": st.column_config.TextColumn("Event Name"),
                "Next Release": st.column_config.DateColumn("Next Scheduled Release (Official)", format="DD/MM/YYYY"),
                "Source": "Data Source",
                "Last Updated": "System Check"
            },
            use_container_width=True,
            height=400,
            hide_index=True
        )
    except FileNotFoundError:
        st.warning("⚠️ Calendar data not found. Please run 'python3 main.py' to generate the schedule.")
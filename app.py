"""
SmartEDA — LLM-Powered Automated Exploratory Data Analysis Tool
Main Streamlit Application

Architecture: Modular, tab-based UI with 7 analysis sections.
LLM Backend: Google Gemini (gemini-1.5-flash / gemini-1.5-pro)
"""

import streamlit as st
import pandas as pd
import numpy as np
import traceback

# ── Page configuration (MUST be first Streamlit call) ────────────────────────
st.set_page_config(
    page_title="SmartEDA — AI-Powered EDA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "SmartEDA: LLM-Powered Automated Exploratory Data Analysis Tool | Built with Google Gemini + Streamlit",
    },
)

# ── Internal modules ──────────────────────────────────────────────────────────
from modules import data_profiler, llm_engine, visualizer, outlier_detector, sql_query, pdf_exporter
from utils.helpers import CARD_CSS, fmt_number, get_quality_badge, dtype_icon

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(CARD_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

def init_session():
    defaults = {
        "df": None,
        "profile": None,
        "profile_text": None,
        "filename": None,
        "gemini_key": "",
        "gemini_model": "gemini-1.5-flash",
        "key_validated": False,
        "insights_text": None,
        "chat_history": [],          # list of {"role": "user"|"assistant", "content": "..."}
        "iqr_result": None,
        "zscore_result": None,
        "corr_fig": None,
        "missing_fig": None,
        "dist_figs": [],
        "cat_figs": [],
        "scatter_figs": [],
        "outlier_figs": [],
        "pairplot_fig": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
        <span style="font-size:2.8rem;">🧠</span>
        <h2 style="color:#6C63FF; margin:0.3rem 0 0; font-size:1.5rem; font-weight:800;">SmartEDA</h2>
        <p style="color:#8B86C8; font-size:0.8rem; margin:0;">LLM-Powered EDA Platform</p>
    </div>
    <hr style="border-color:rgba(108,99,255,0.25); margin: 1rem 0;">
    """, unsafe_allow_html=True)

    # ── File Upload ────────────────────────────────────────────────────────
    st.markdown("### 📁 Upload Dataset")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload any CSV dataset up to 200 MB",
        label_visibility="collapsed",
    )

    # ── Gemini API Key ─────────────────────────────────────────────────────
    st.markdown("### 🔑 Gemini API Key")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=st.session_state.gemini_key,
        type="password",
        placeholder="AIzaSy...",
        help="Get your free key at https://aistudio.google.com/",
        label_visibility="collapsed",
    )
    if api_key_input != st.session_state.gemini_key:
        st.session_state.gemini_key = api_key_input
        st.session_state.key_validated = False

    col_v, col_m = st.columns([1, 1])
    with col_v:
        if st.button("✔ Validate", use_container_width=True, type="secondary"):
            if st.session_state.gemini_key:
                with st.spinner("Validating..."):
                    ok, msg = llm_engine.validate_api_key(st.session_state.gemini_key)
                    st.session_state.key_validated = ok
                if ok:
                    st.success("✓ Valid")
                else:
                    st.error(msg)
            else:
                st.warning("Enter an API key first.")

    if st.session_state.key_validated:
        st.markdown('<div style="color:#00C853;font-size:0.8rem;">✓ API key active</div>', unsafe_allow_html=True)

    # ── Model Selection ────────────────────────────────────────────────────
    st.markdown("### 🤖 Gemini Model")
    model_choice = st.selectbox(
        "Select Gemini model",
        options=llm_engine.list_available_models(),
        index=0,
        label_visibility="collapsed",
    )
    st.session_state.gemini_model = model_choice

    st.markdown('<hr style="border-color:rgba(108,99,255,0.2);">', unsafe_allow_html=True)

    # ── Dataset Info (after upload) ────────────────────────────────────────
    if st.session_state.df is not None:
        df = st.session_state.df
        profile = st.session_state.profile
        quality_label, quality_color = get_quality_badge(
            profile["missing_info"]["Missing %"].max() if not profile["missing_info"].empty else 0,
            profile["duplicate_pct"],
        )
        st.markdown(f"""
        <div style="background:rgba(26,29,46,0.8); border-radius:12px; padding:1rem; border:1px solid rgba(108,99,255,0.2);">
            <div style="font-size:0.75rem; color:#8B86C8; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Active Dataset</div>
            <div style="font-size:0.9rem; color:#E0DEFC; font-weight:600; margin-bottom:0.3rem;">📄 {st.session_state.filename}</div>
            <div style="font-size:0.82rem; color:#7A7A9A;">{profile['n_rows']:,} rows × {profile['n_cols']} columns</div>
            <div style="margin-top:0.5rem;">
                <span class="quality-badge" style="background:{quality_color}22; color:{quality_color}; border:1px solid {quality_color}55;">
                    {quality_label} Quality
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑 Clear Dataset", use_container_width=True, type="secondary"):
            for key in ["df", "profile", "profile_text", "filename", "insights_text",
                        "chat_history", "iqr_result", "zscore_result",
                        "corr_fig", "missing_fig", "dist_figs", "cat_figs",
                        "scatter_figs", "outlier_figs", "pairplot_fig"]:
                st.session_state[key] = None if key not in ["chat_history", "dist_figs", "cat_figs", "scatter_figs", "outlier_figs"] else []
            st.rerun()

    st.markdown("""
    <div style="margin-top:2rem; text-align:center; color:#4A4A6A; font-size:0.72rem;">
        SmartEDA v1.0 · Built with ❤️ using<br>Streamlit + Google Gemini + Plotly
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILE PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

if uploaded_file is not None:
    if st.session_state.filename != uploaded_file.name:
        # New file uploaded — process it
        with st.spinner(f"⚙️ Profiling **{uploaded_file.name}** ..."):
            try:
                df = data_profiler.load_csv(uploaded_file)
                profile = data_profiler.full_profile(df)
                profile_text = data_profiler.profile_to_text(profile, df)

                # Pre-generate all visualizations
                dist_figs = visualizer.plot_distribution_histograms(
                    df, profile["column_types"]["numeric"]
                )
                cat_figs = visualizer.plot_categorical_bar_charts(
                    df, profile["column_types"]["categorical"]
                )
                corr_fig = visualizer.plot_correlation_heatmap(profile["corr_matrix"])
                missing_fig = visualizer.plot_missing_values(profile["missing_info"])
                scatter_figs = visualizer.plot_scatter_high_correlation(
                    df, profile["top_correlations"]
                )
                pairplot_fig = visualizer.plot_pairplot_matrix(
                    df, profile["column_types"]["numeric"]
                )

                # Store in session
                st.session_state.df = df
                st.session_state.profile = profile
                st.session_state.profile_text = profile_text
                st.session_state.filename = uploaded_file.name
                st.session_state.dist_figs = dist_figs
                st.session_state.cat_figs = cat_figs
                st.session_state.corr_fig = corr_fig
                st.session_state.missing_fig = missing_fig
                st.session_state.scatter_figs = scatter_figs
                st.session_state.pairplot_fig = pairplot_fig
                st.session_state.insights_text = None
                st.session_state.chat_history = []
                st.session_state.iqr_result = None
                st.session_state.zscore_result = None
                st.session_state.outlier_figs = []

                st.success(f"✅ Dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")

            except Exception as e:
                st.error(f"❌ Failed to load or profile the dataset: {e}")
                st.code(traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="smarteda-header">
    <h1>🧠 SmartEDA</h1>
    <p>LLM-Powered Automated Exploratory Data Analysis — Upload any CSV and let AI do the work</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.df is None:
    # Landing state — no file uploaded
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem 2rem;">
        <div style="font-size:5rem; margin-bottom:1rem;">📊</div>
        <h2 style="color:#6C63FF; font-weight:700; margin-bottom:0.5rem;">Get Started</h2>
        <p style="color:#8B86C8; font-size:1.05rem; max-width:520px; margin:0 auto;">
            Upload a CSV file from the sidebar to begin your automated analysis.
            SmartEDA will profile your data, generate visualizations, and provide
            AI-powered insights — no coding required.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature Cards
    cols = st.columns(4)
    features = [
        ("📊", "Data Profiling", "Comprehensive stats: shape, missing values, skewness, kurtosis, cardinality and more."),
        ("📈", "Auto Visualizations", "6+ chart types: histograms, heatmaps, scatter plots, bar charts, pair plots."),
        ("🤖", "AI Insights", "Gemini-powered narrative EDA reports with ML recommendations in plain English."),
        ("💬", "Chat with Data", "Ask natural-language questions about your dataset in a multi-turn conversation."),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="padding:1.5rem; text-align:center;">
                <div style="font-size:2.2rem; margin-bottom:0.8rem;">{icon}</div>
                <div style="color:#6C63FF; font-weight:700; font-size:1rem; margin-bottom:0.5rem;">{title}</div>
                <div style="color:#7A7A9A; font-size:0.84rem; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    cols2 = st.columns(3)
    features2 = [
        ("🔍", "Outlier Detection", "IQR + Z-score based outlier analysis with visual box plots."),
        ("🗃️", "SQL Queries", "Write SQL directly against your uploaded dataset using pandasql."),
        ("📄", "PDF Export", "Download a comprehensive analysis report as a formatted PDF."),
    ]
    for col, (icon, title, desc) in zip(cols2, features2):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="padding:1.5rem; text-align:center;">
                <div style="font-size:2.2rem; margin-bottom:0.8rem;">{icon}</div>
                <div style="color:#6C63FF; font-weight:700; font-size:1rem; margin-bottom:0.5rem;">{title}</div>
                <div style="color:#7A7A9A; font-size:0.84rem; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# TABS — Only rendered when a dataset is loaded
# ══════════════════════════════════════════════════════════════════════════════

df = st.session_state.df
profile = st.session_state.profile

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Data Overview",
    "📈 Visualizations",
    "🤖 AI Insights",
    "💬 Chat",
    "🔍 Outlier Detection",
    "🗃️ SQL Query",
    "📄 Export PDF",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DATA OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    # ── Top Metric Cards ──────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    metric_data = [
        (m1, "Rows", f"{profile['n_rows']:,}", None),
        (m2, "Columns", str(profile['n_cols']), None),
        (m3, "Missing", f"{profile['missing_info']['Missing %'].max():.1f}%", "max in any column"),
        (m4, "Duplicates", f"{profile['duplicate_count']:,}", f"{profile['duplicate_pct']:.1f}%"),
        (m5, "Memory", f"{profile['memory_usage_mb']} MB", None),
    ]
    for col, label, value, delta in metric_data:
        with col:
            st.metric(label=label, value=value, delta=delta)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Column Type Summary ───────────────────────────────────────────────
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 🗂 Column Types")
        type_summary = {
            "Type": ["Numeric", "Categorical", "Datetime"],
            "Count": [
                len(profile["column_types"]["numeric"]),
                len(profile["column_types"]["categorical"]),
                len(profile["column_types"]["datetime"]),
            ],
        }
        st.dataframe(
            pd.DataFrame(type_summary),
            use_container_width=True,
            hide_index=True,
        )

    with c2:
        st.markdown("#### 🏷 Column Info")
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str),
            "Non-Null": df.count().values,
            "Null %": (df.isnull().mean() * 100).round(2).values,
            "Unique": df.nunique().values,
        })
        col_info.insert(0, "Icon", col_info["Type"].apply(dtype_icon))
        st.dataframe(col_info, use_container_width=True, hide_index=True, height=220)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Missing Values ────────────────────────────────────────────────────
    st.markdown("#### ❓ Missing Values")
    missing_df = profile["missing_info"]
    has_missing = missing_df[missing_df["Missing Count"] > 0]
    if has_missing.empty:
        st.markdown('<div class="info-box">✅ No missing values detected in this dataset.</div>', unsafe_allow_html=True)
    else:
        st.dataframe(has_missing, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Descriptive Statistics ────────────────────────────────────────────
    st.markdown("#### 📐 Descriptive Statistics")
    desc_stats = profile["desc_stats"]
    if not desc_stats.empty:
        st.dataframe(desc_stats, use_container_width=True, hide_index=True)
    else:
        st.info("No numeric columns to display statistics for.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Cardinality ───────────────────────────────────────────────────────
    st.markdown("#### 🔢 Cardinality")
    st.dataframe(profile["cardinality"], use_container_width=True, hide_index=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Top Correlations ──────────────────────────────────────────────────
    st.markdown("#### 🔗 Top Correlations (|r| ≥ 0.5)")
    top_corr = profile["top_correlations"]
    if not top_corr.empty:
        st.dataframe(top_corr, use_container_width=True, hide_index=True)
    else:
        st.info("No strong correlations (|r| ≥ 0.5) found.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Preview Table ─────────────────────────────────────────────────────
    st.markdown("#### 👁 Dataset Preview")
    preview_rows = st.slider("Rows to preview", 5, min(200, len(df)), 10, key="preview_slider")
    st.dataframe(df.head(preview_rows), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    viz_choice = st.radio(
        "Chart Category",
        options=["📊 Distributions", "🔥 Correlation Heatmap", "🏷 Categorical", "❓ Missing Values", "🔗 Scatter Plots", "📐 Pair Plot"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if viz_choice == "📊 Distributions":
        numeric_cols = profile["column_types"]["numeric"]
        if not numeric_cols:
            st.info("No numeric columns available for distribution plots.")
        else:
            st.markdown(f"#### Distribution Histograms — {len(numeric_cols)} numeric column(s)")
            dist_figs = st.session_state.dist_figs
            if not dist_figs:
                st.info("No distribution figures generated.")
            else:
                # Show 2 at a time in columns
                for i in range(0, len(dist_figs), 2):
                    cols_pair = st.columns(2)
                    for j, c in enumerate(cols_pair):
                        if i + j < len(dist_figs):
                            col_name, fig = dist_figs[i + j]
                            with c:
                                st.plotly_chart(fig, use_container_width=True, key=f"dist_{col_name}")

    elif viz_choice == "🔥 Correlation Heatmap":
        corr_fig = st.session_state.corr_fig
        if corr_fig is None:
            st.info("Not enough numeric columns to generate a correlation heatmap (need ≥ 2).")
        else:
            st.markdown("#### Pearson Correlation Heatmap")
            st.plotly_chart(corr_fig, use_container_width=True, key="corr_heatmap")
            # Also show top correlations table
            top_c = profile["top_correlations"]
            if not top_c.empty:
                st.markdown("**Strongly Correlated Pairs (|r| ≥ 0.5)**")
                st.dataframe(top_c, use_container_width=True, hide_index=True)

    elif viz_choice == "🏷 Categorical":
        cat_figs = st.session_state.cat_figs
        if not cat_figs:
            st.info("No categorical columns found.")
        else:
            st.markdown(f"#### Categorical Distributions — {len(cat_figs)} column(s)")
            for i in range(0, len(cat_figs), 2):
                cols_pair = st.columns(2)
                for j, c in enumerate(cols_pair):
                    if i + j < len(cat_figs):
                        col_name, fig = cat_figs[i + j]
                        with c:
                            st.plotly_chart(fig, use_container_width=True, key=f"cat_{col_name}")

    elif viz_choice == "❓ Missing Values":
        missing_fig = st.session_state.missing_fig
        if missing_fig is None:
            st.markdown('<div class="info-box">✅ No missing values in this dataset — nothing to visualize.</div>', unsafe_allow_html=True)
        else:
            st.markdown("#### Missing Values Visualization")
            st.plotly_chart(missing_fig, use_container_width=True, key="missing_chart")

    elif viz_choice == "🔗 Scatter Plots":
        scatter_figs = st.session_state.scatter_figs
        if not scatter_figs:
            st.info("No high-correlation column pairs found (|r| ≥ 0.5). Scatter plots require at least 2 correlated numeric columns.")
        else:
            st.markdown(f"#### Scatter Plots for High-Correlation Pairs ({len(scatter_figs)} pair(s))")
            for i in range(0, len(scatter_figs), 2):
                cols_pair = st.columns(2)
                for j, c in enumerate(cols_pair):
                    if i + j < len(scatter_figs):
                        pair_name, fig = scatter_figs[i + j]
                        with c:
                            st.plotly_chart(fig, use_container_width=True, key=f"scatter_{pair_name}")

    elif viz_choice == "📐 Pair Plot":
        pairplot_fig = st.session_state.pairplot_fig
        if pairplot_fig is None:
            st.info("Need ≥ 2 numeric columns to generate a pair plot.")
        else:
            st.markdown("#### Scatter Matrix (Pair Plot) — First 5 Numeric Columns")
            st.plotly_chart(pairplot_fig, use_container_width=True, key="pairplot")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("#### 🤖 AI-Generated EDA Report")
    st.markdown("""
    <div class="info-box">
        Gemini will analyze your dataset profile and generate a comprehensive narrative report including 
        dataset summary, data quality assessment, statistical observations, correlation analysis, 
        preprocessing recommendations, and ML model suggestions.
    </div>
    """, unsafe_allow_html=True)

    # ── Generate / Regenerate Button ──────────────────────────────────────
    col_gen, col_model = st.columns([2, 1])
    with col_gen:
        gen_btn = st.button(
            "🚀 Generate AI Insights" if not st.session_state.insights_text else "🔄 Regenerate Insights",
            type="primary",
            use_container_width=True,
            key="gen_insights_btn",
        )
    with col_model:
        st.markdown(f"<div style='padding:0.6rem; background:rgba(108,99,255,0.1); border-radius:8px; font-size:0.85rem; color:#8B86C8; text-align:center;'>Model: {st.session_state.gemini_model}</div>", unsafe_allow_html=True)

    if gen_btn:
        if not st.session_state.gemini_key:
            st.error("❌ Please enter your Gemini API key in the sidebar first.")
        else:
            with st.spinner("🧠 Gemini is analyzing your dataset..."):
                try:
                    insights = llm_engine.generate_insights(
                        profile_text=st.session_state.profile_text,
                        api_key=st.session_state.gemini_key,
                        model_name=st.session_state.gemini_model,
                    )
                    st.session_state.insights_text = insights
                    st.success("✅ Insights generated successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to generate insights: {e}")
                    st.code(traceback.format_exc())

    # ── Display Insights ──────────────────────────────────────────────────
    if st.session_state.insights_text:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(st.session_state.insights_text)
    elif not gen_btn:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#4A4A6A;">
            <div style="font-size:3rem; margin-bottom:1rem;">🤖</div>
            <p>Click "Generate AI Insights" above to receive your AI-powered EDA report.</p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CHAT
# ══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.markdown("#### 💬 Chat with Your Data")
    st.markdown("""
    <div class="info-box">
        Ask natural-language questions about your dataset. Gemini will answer with text explanations 
        and Pandas code snippets where appropriate. Full conversation history is maintained.
    </div>
    """, unsafe_allow_html=True)

    # ── Chat history display ──────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; padding:2rem; color:#4A4A6A;">
                <div style="font-size:2.5rem; margin-bottom:0.5rem;">💬</div>
                <p>Start by asking a question about your data!</p>
                <p style="font-size:0.85rem;">Examples: "Which column has the most missing values?", 
                "What is the average age by gender?", "Which features are most correlated?"</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div style="display:flex; justify-content:flex-end; margin-bottom:0.5rem;">
                        <div class="chat-user">👤 {msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-assistant" style="font-size:0.9rem;">', unsafe_allow_html=True)
                    st.markdown(msg["content"])
                    st.markdown('</div>', unsafe_allow_html=True)

    # ── Chat input ────────────────────────────────────────────────────────
    st.markdown("")
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_question = st.text_input(
            "Ask a question",
            placeholder="e.g. Which column has the most outliers? What ML model should I use?",
            key="chat_input",
            label_visibility="collapsed",
        )
    with col_send:
        send_btn = st.button("Send ➤", type="primary", use_container_width=True, key="send_chat")

    # Example prompts
    st.markdown("**Quick questions:**")
    eq_cols = st.columns(4)
    example_qs = [
        "What is the overall data quality?",
        "Which columns have the most outliers?",
        "What preprocessing steps do you recommend?",
        "Which ML model would work best here?",
    ]
    for i, (col, q) in enumerate(zip(eq_cols, example_qs)):
        with col:
            if st.button(q, key=f"example_q_{i}", use_container_width=True, type="secondary"):
                user_question = q
                send_btn = True

    if send_btn and user_question.strip():
        if not st.session_state.gemini_key:
            st.error("❌ Please enter your Gemini API key in the sidebar first.")
        else:
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": user_question.strip()})

            with st.spinner("🧠 Thinking..."):
                try:
                    # Build history without the latest user message (already appended)
                    history_for_api = st.session_state.chat_history[:-1]
                    response = llm_engine.chat_with_data(
                        user_message=user_question.strip(),
                        conversation_history=history_for_api,
                        profile_text=st.session_state.profile_text,
                        api_key=st.session_state.gemini_key,
                        model_name=st.session_state.gemini_model,
                    )
                    st.session_state.chat_history.append({"role": "model", "content": response})
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Chat error: {e}")

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑 Clear Chat History", type="secondary", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — OUTLIER DETECTION
# ══════════════════════════════════════════════════════════════════════════════

with tab5:
    st.markdown("#### 🔍 Outlier Detection")

    numeric_cols = profile["column_types"]["numeric"]
    if not numeric_cols:
        st.info("No numeric columns available for outlier detection.")
    else:
        # Settings
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            iqr_mult = st.slider("IQR Multiplier", 1.0, 3.0, 1.5, 0.1,
                                  help="Rows outside Q1 - mult*IQR or Q3 + mult*IQR are flagged", key="iqr_mult")
        with col_s2:
            z_thresh = st.slider("Z-Score Threshold", 1.5, 5.0, 3.0, 0.1,
                                  help="Rows with |z| > threshold are flagged", key="z_thresh")
        with col_s3:
            run_btn = st.button("▶ Run Outlier Detection", type="primary", use_container_width=True, key="run_outliers")

        if run_btn:
            with st.spinner("Detecting outliers..."):
                iqr_res = outlier_detector.detect_outliers_iqr(df, multiplier=iqr_mult)
                zscore_res = outlier_detector.detect_outliers_zscore(df, threshold=z_thresh)

                # Generate outlier box plots
                outlier_figs = visualizer.plot_outlier_boxplots(df, iqr_res.get("bounds", {}), numeric_cols)

                st.session_state.iqr_result = iqr_res
                st.session_state.zscore_result = zscore_res
                st.session_state.outlier_figs = outlier_figs

        iqr_res = st.session_state.iqr_result
        zscore_res = st.session_state.zscore_result

        if iqr_res is None:
            st.markdown("""
            <div style="text-align:center; padding:2.5rem; color:#4A4A6A;">
                <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔍</div>
                <p>Click "Run Outlier Detection" above to analyze outliers.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # ── Summary Cards ─────────────────────────────────────────────
            sm1, sm2, sm3 = st.columns(3)
            with sm1:
                st.metric("IQR Flagged Rows", f"{iqr_res['n_flagged']:,}",
                           delta=f"{iqr_res['n_flagged']/len(df)*100:.1f}%")
            with sm2:
                st.metric("Z-Score Flagged Rows", f"{zscore_res['n_flagged']:,}",
                           delta=f"{zscore_res['n_flagged']/len(df)*100:.1f}%")
            with sm3:
                max_col = iqr_res["summary"].iloc[0]["Column"] if not iqr_res["summary"].empty else "N/A"
                max_count = iqr_res["summary"].iloc[0]["Outlier Count"] if not iqr_res["summary"].empty else 0
                st.metric("Most Outlier-Prone Col", max_col, delta=f"{max_count} outliers")

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            # ── IQR Table ─────────────────────────────────────────────────
            st.markdown("##### IQR Method Results")
            st.dataframe(iqr_res["summary"], use_container_width=True, hide_index=True)

            # ── Z-Score Table ─────────────────────────────────────────────
            st.markdown("##### Z-Score Method Results")
            st.dataframe(zscore_res["summary"], use_container_width=True, hide_index=True)

            # ── Flagged Rows Preview ───────────────────────────────────────
            if not iqr_res["flagged_rows"].empty:
                with st.expander(f"📋 View {len(iqr_res['flagged_rows'])} IQR-Flagged Rows", expanded=False):
                    st.dataframe(iqr_res["flagged_rows"].head(200), use_container_width=True, hide_index=True)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            # ── Outlier Box Plots ─────────────────────────────────────────
            outlier_figs = st.session_state.outlier_figs
            if outlier_figs:
                st.markdown("##### Outlier Visualizations (IQR Box Plots)")
                for i in range(0, len(outlier_figs), 3):
                    cols_trio = st.columns(3)
                    for j, c in enumerate(cols_trio):
                        if i + j < len(outlier_figs):
                            col_name, fig = outlier_figs[i + j]
                            with c:
                                st.plotly_chart(fig, use_container_width=True, key=f"outlier_box_{col_name}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — SQL QUERY
# ══════════════════════════════════════════════════════════════════════════════

with tab6:
    st.markdown("#### 🗃️ SQL Query Interface")
    st.markdown("""
    <div class="info-box">
        Query your dataset using standard SQL. The table name is <code>df</code>. 
        All standard SELECT operations are supported via pandasql.
    </div>
    """, unsafe_allow_html=True)

    # ── Examples ──────────────────────────────────────────────────────────
    st.markdown("**Example Queries:**")
    examples = sql_query.get_sql_examples(df.columns.tolist())
    example_cols = st.columns(len(examples))
    selected_example = None
    for i, (col, ex) in enumerate(zip(example_cols, examples)):
        with col:
            if st.button(f"📋 Example {i+1}", key=f"sql_ex_{i}", use_container_width=True, type="secondary"):
                selected_example = ex

    # ── SQL Editor ────────────────────────────────────────────────────────
    default_sql = selected_example or f"SELECT * FROM df LIMIT 10"
    sql_text = st.text_area(
        "Write your SQL query",
        value=default_sql,
        height=120,
        key="sql_editor",
        placeholder="SELECT column1, COUNT(*) FROM df GROUP BY column1",
        label_visibility="collapsed",
    )

    col_run, col_clear = st.columns([2, 1])
    with col_run:
        run_sql = st.button("▶ Execute Query", type="primary", use_container_width=True, key="run_sql_btn")
    with col_clear:
        if st.button("🗑 Clear", use_container_width=True, type="secondary", key="clear_sql"):
            st.rerun()

    # ── Column Reference ──────────────────────────────────────────────────
    with st.expander("📋 Column Reference", expanded=False):
        col_ref = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str),
            "Sample": [str(df[c].dropna().iloc[0]) if df[c].dropna().shape[0] > 0 else "N/A" for c in df.columns],
        })
        st.dataframe(col_ref, use_container_width=True, hide_index=True)

    # ── Query Execution ───────────────────────────────────────────────────
    if run_sql and sql_text.strip():
        with st.spinner("⚙️ Running query..."):
            result_df, error = sql_query.run_sql_query(df, sql_text.strip())

        if error:
            st.error(f"❌ {error}")
        elif result_df is not None:
            st.success(f"✅ Query returned {len(result_df):,} rows × {result_df.shape[1]} columns")
            st.dataframe(result_df, use_container_width=True)

            # Download result
            csv_data = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Query Result as CSV",
                data=csv_data,
                file_name="smarteda_query_result.csv",
                mime="text/csv",
                key="dl_sql_result",
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — EXPORT PDF
# ══════════════════════════════════════════════════════════════════════════════

with tab7:
    st.markdown("#### 📄 Export Full EDA Report as PDF")
    st.markdown("""
    <div class="info-box">
        Generate a comprehensive PDF report containing the dataset overview, statistical summaries, 
        correlation analysis, outlier detection results, AI-generated insights, and key visualizations.
    </div>
    """, unsafe_allow_html=True)

    # ── What's included ───────────────────────────────────────────────────
    st.markdown("**Report Contents:**")
    c1, c2, c3 = st.columns(3)
    contents = [
        (c1, ["📊 Dataset Overview", "❓ Missing Values Summary", "📐 Descriptive Statistics"]),
        (c2, ["🔗 Correlation Analysis", "🔍 Outlier Detection Summary", "📈 Key Visualizations"]),
        (c3, ["🤖 AI Insights (if generated)", "📁 File Metadata", "📋 Full Statistical Report"]),
    ]
    for col, items in contents:
        with col:
            for item in items:
                st.markdown(f"✓ {item}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── AI Insights Notice ────────────────────────────────────────────────
    if not st.session_state.insights_text:
        st.warning("⚠️ AI Insights not yet generated. Generate them in the **AI Insights** tab to include them in the PDF report.")

    if not st.session_state.iqr_result:
        st.info("ℹ️ Run Outlier Detection in the **Outlier Detection** tab to include outlier results in the PDF.")

    # ── Generate PDF ──────────────────────────────────────────────────────
    st.markdown("")
    if st.button("📄 Generate PDF Report", type="primary", use_container_width=False, key="gen_pdf_btn"):
        with st.spinner("📝 Generating your PDF report... This may take a moment for charts."):
            try:
                pdf_bytes = pdf_exporter.generate_pdf_report(
                    profile=st.session_state.profile,
                    df=df,
                    insights_text=st.session_state.insights_text,
                    corr_fig=st.session_state.corr_fig,
                    missing_fig=st.session_state.missing_fig,
                    dist_figs=st.session_state.dist_figs,
                    outlier_iqr=st.session_state.iqr_result,
                )

                report_name = f"SmartEDA_Report_{st.session_state.filename.replace('.csv', '')}.pdf"
                st.success("✅ PDF generated successfully!")
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=report_name,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=False,
                    key="dl_pdf_btn",
                )
            except ImportError as e:
                st.error(f"❌ {e}")
            except Exception as e:
                st.error(f"❌ Failed to generate PDF: {e}")
                st.code(traceback.format_exc())

---
title: SmartEDA
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: LLM-Powered Automated Exploratory Data Analysis Tool
---

# 🧠 SmartEDA — LLM-Powered Automated EDA Tool

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.19+-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

**Upload any CSV. Get full EDA in seconds. No code required.**

</div>

---

## Overview

SmartEDA is an AI-powered Exploratory Data Analysis platform. Upload a CSV dataset and instantly get statistical profiling, interactive visualizations, Gemini-generated narrative insights, and a conversational interface to query your data in plain English — all without writing a single line of code.

---

## Features

| Tab | What it does |
|-----|-------------|
| 📊 **Data Overview** | Shape, missing values, descriptive stats, skewness, kurtosis, correlations |
| 📈 **Visualizations** | Histograms, heatmap, bar charts, scatter plots, pair plot (Plotly) |
| 🤖 **AI Insights** | Gemini-generated narrative report with ML recommendations |
| 💬 **Chat** | Multi-turn natural language Q&A about your dataset |
| 🔍 **Outlier Detection** | IQR + Z-score methods with visual box plots |
| 🗃️ **SQL Query** | Write SQL directly against your uploaded dataset |
| 📄 **Export PDF** | Download a full analysis report as a PDF |

---

## Installation

```bash
git clone https://github.com/yourusername/smartEDA.git
cd smartEDA
pip install -r requirements.txt
streamlit run app.py
```

App runs at **http://localhost:8501**

> Get a free Gemini API key at [https://aistudio.google.com/](https://aistudio.google.com/)

---

## Project Structure

```
smartEDA/
├── app.py                   # Main Streamlit app (7 tabs)
├── requirements.txt
├── .streamlit/config.toml   # Dark theme config
├── modules/
│   ├── data_profiler.py     # Statistical profiling
│   ├── llm_engine.py        # Google Gemini integration
│   ├── visualizer.py        # Plotly charts
│   ├── outlier_detector.py  # IQR + Z-score detection
│   ├── sql_query.py         # pandasql interface
│   └── pdf_exporter.py      # PDF report generation
└── utils/
    └── helpers.py           # Utilities + CSS
```

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| UI | Streamlit |
| LLM | Google Gemini (2.5 Flash / 1.5 Pro) |
| Data | Pandas, NumPy, SciPy |
| Visualization | Plotly, Seaborn |
| ML / Stats | Scikit-learn |
| SQL | pandasql |
| PDF Export | FPDF2, kaleido |
| Language | Python 3.11+ |

---

## Requirements

- Python 3.11+
- 8 GB RAM minimum
- Internet connection (for Gemini API)
- No GPU required

---

## Privacy

Your CSV is processed **entirely locally**. Only the statistical profile (not raw data) is sent to the Gemini API. No data is stored or logged.

---

## Academic Context

Developed as a B.Tech final-year project — *Department of Computer Science & Engineering (AI), Gurugram University, Jan–May 2026.*

---

<div align="center">
Built with ❤️ using Streamlit + Google Gemini + Plotly
</div>

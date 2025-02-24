import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
from streamlit_pdf import pdf  # Optional for PDF export, install with `pip install streamlit-pdf`

# App Title
st.title("LunkerAI: Fisheries Data Analysis")
st.subheader("Monitoring Report Generator for Red Fleet Reservoir")

# Standard Weight Formula Parameters (Updated for Red Fleet species)
species_ws_params = {
    "Walleye": (-5.453, 3.180, 250),  # S=250, Q=380, P=510, M=630, T=760
    "Wiper": (-5.843, 3.436, 150),  # S=150, Q=230, P=300, M=380, T=460
    "Smallmouth Bass": (-5.329, 3.200, 150),  # Assuming for SMB, adjust if needed
    "Largemouth Bass": (-5.528, 3.273, 200),  # S=200, Q=300, P=380, M=510, T=630
    "Bluegill": (-5.374, 3.316, 80),  # S=80, Q=150, P=200, M=250, T=300
    "Black Crappie": (-5.504, 3.288, 130),  # S=130, Q=200, P=250, M=300, T=380
    "Yellow Perch": (-5.386, 3.230, 130),  # S=130, Q=200, P=250, M=300, T=380
    "Brown Trout": (-5.621, 3.358, 200),  # S=200, Q=300, P=400, M=500, T=600
    "Rainbow Trout": (-5.598, 3.357, 250)  # S=250, Q=400, P=500, M=650, T=800
}

# PSD Thresholds (Updated for Red Fleet species)
psd_thresholds = {
    "Walleye": (250, 380, 510, 630, 760),  # S, Q, P, M, T
    "Wiper": (150, 230, 300, 380, 460),
    "Smallmouth Bass": (150, 250, 350, 450, 550),  # Default, adjust if needed
    "Largemouth Bass": (200, 300, 380, 510, 630),
    "Bluegill": (80, 150, 200, 250, 300),
    "Black Crappie": (130, 200, 250, 300, 380),
    "Yellow Perch": (130, 200, 250, 300, 380),
    "Brown Trout": (200, 300, 400, 500, 600),
    "Rainbow Trout": (250, 400, 500, 650, 800)
}


# Function to calculate standard weight (Ws)
@st.cache_data
def calculate_standard_weight(species, length):
    if species in species_ws_params and length >= species_ws_params[species][2]:
        a, b, _ = species_ws_params[species]
        return 10 ** (a + b * np.log10(length))
    return np.nan


# Function to calculate PSD
@st.cache_data
def calculate_psd(lengths, species):
    if species not in psd_thresholds:
        return [0, 0, 0, 0, 0]  # Default to 0 if species not found
    s, q, p, m, t = psd_thresholds[species]
    stock = len(lengths[lengths >= s])
    if stock == 0:
        return [0, 0, 0, 0, 0]
    quality = len(lengths[lengths >= q]) / stock * 100
    preferred = len(lengths[lengths >= p]) / stock * 100
    memorable = len(lengths[lengths >= m]) / stock * 100
    trophy = len(lengths[lengths >= t]) / stock * 100
    return [quality, preferred, memorable, trophy]


# File Upload
uploaded_file = st.file_uploader("Upload Fisheries Data (Excel)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.write("### Uploaded Data Preview:")
        st.dataframe(df.head())

        # Select required columns with default values
        species_column = st.selectbox("Select Species Column:", df.columns,
                                      index=df.columns.get_loc("Species") if "Species" in df.columns else 0)
        length_column = st.selectbox("Select Fish Length Column (mm):", df.columns,
                                     index=df.columns.get_loc("TL_mm") if "TL_mm" in df.columns else 0)
        weight_column = st.selectbox("Select Fish Weight Column (g):", df.columns,
                                     index=df.columns.get_loc("WT_g") if "WT_g" in df.columns else 0)
        effort_column = st.selectbox("Select Effort Column (Hours):", df.columns,
                                     index=df.columns.get_loc("Effort_Hr") if "Effort_Hr" in df.columns else 0)
        temp_column = st.selectbox("Select Water Temperature Column (°F or °C):", df.columns,
                                   index=df.columns.get_loc("Water_Temp_F") if "Water_Temp_F" in df.columns else 0)
        conductivity_column = st.selectbox("Select Conductivity Column (µS):", df.columns, index=df.columns.get_loc(
            "Conductivity_um") if "Conductivity_um" in df.columns else 0)
        ph_column = st.selectbox("Select pH Column:", df.columns,
                                 index=df.columns.get_loc("pH") if "pH" in df.columns else 0)

        if st.button("Generate Monitoring Report"):
            # Validate required columns
            required_columns = [species_column, length_column, weight_column, effort_column]
            if any(col not in df.columns for col in required_columns):
                st.error("Missing required columns (Species, Length, Weight, Effort). Please check your Excel file.")
                return

            # Calculate CPUE and Abundance
            effort = df[effort_column].sum()
            if effort <= 0:
                st.error("Effort must be greater than 0.")
                return
            species_groups = df.groupby(species_column)

            # Abundance, Condition, and PSD Table
            abundance_data = []
            for species, group in species_groups:
                cpue = len(group) / effort
                mean_tl = group[length_column].mean()
                range_tl = f"{group[length_column].min()}-{group[length_column].max()}"
                mean_wt = group[weight_column].mean()
                range_wt = f"{group[weight_column].min()}-{group[weight_column].max()}"
                wr_values = [calculate_standard_weight(species, l) for l in group[length_column] if not pd.isna(l)]
                mean_wr = np.nanmean([w / calculate_standard_weight(species, l) * 100 for w, l in
                                      zip(group[weight_column], group[length_column]) if
                                      not pd.isna(w) and not pd.isna(l) and not pd.isna(
                                          calculate_standard_weight(species, l))])
                psd_values = calculate_psd(group[length_column].dropna(), species)
                abundance_data.append(
                    [species, cpue, mean_tl, range_tl, mean_wt, range_wt, mean_wr if not pd.isna(mean_wr) else 0,
                     *psd_values])

            abundance_df = pd.DataFrame(abundance_data,
                                        columns=["Target Species", "CPUE Fish/Hr", "Mean TL", "Range TL", "Mean WT",
                                                 "Range WT", "Mean Wr", "PSD-S/Q", "PSD-S/P", "PSD-S/M", "PSD-S/T"])
            st.write("### Abundance, Condition, and Proportional Size Distribution of Target Species")
            st.table(abundance_df.round(2))

            # Catch Summary Table
            catch_data = []
            total_number = len(df)
            total_biomass = df[weight_column].sum() / 1000  # Convert to kg
            for species, group in species_groups:
                number = len(group)
                number_pct = (number / total_number) * 100
                biomass = group[weight_column].sum() / 1000  # Convert to kg
                biomass_pct = (biomass / total_biomass) * 100 if total_biomass > 0 else 0
                catch_data.append([species, number, number_pct, biomass, biomass_pct])

            catch_df = pd.DataFrame(catch_data, columns=["Species", "Number", "Number %", "Biomass (kg)", "Biomass %"])
            st.write("### Catch Summary")
            st.table(catch_df.round(2))

            # Water Quality (if columns exist)
            if conductivity_column in df.columns and ph_column in df.columns:
                water_quality = df[[conductivity_column, ph_column]].mean().round(2)
                if temp_column in df.columns:
                    water_quality["Temp (°F)"] = df[temp_column].mean().round(2)
                st.write("### Water Quality")
                st.table(water_quality.to_frame().T)

            # Length Frequency Histogram
            species_select = st.selectbox("Select Species for Length Frequency:",
                                          abundance_df["Target Species"].unique())
            if st.button("Generate Length Frequency Histogram"):
                lengths = df[df[species_column] == species_select][length_column].dropna()
                if len(lengths) > 0:
                    plt.figure(figsize=(8, 5))
                    plt.hist(lengths, bins=20, color='blue', edgecolor='black')
                    plt.xlabel("Fish Length (mm)")
                    plt.ylabel("Frequency")
                    plt.title(f"Length Frequency Distribution for {species_select}")
                    st.pyplot(plt)
                else:
                    st.error("No length data available for this species.")

            # Length-Weight Regression
            if st.button("Generate Length-Weight Regression"):
                lengths = df[df[species_column] == species_select][length_column].dropna()
                weights = df[df[species_column] == species_select][weight_column].dropna()
                if len(lengths) > 1 and len(weights) > 1:
                    slope, intercept, r_value, _, _ = linregress(np.log10(lengths), np.log10(weights))
                    x = np.linspace(min(lengths), max(lengths), 100)
                    y = 10 ** (intercept + slope * np.log10(x))
                    plt.figure(figsize=(8, 5))
                    plt.scatter(lengths, weights, color='blue', alpha=0.5, label='Data Points')
                    plt.plot(x, y, color='red', label=f'R² = {r_value ** 2:.3f}')
                    plt.xlabel("Total Length (mm)")
                    plt.ylabel("Weight (g)")
                    plt.title(f"Length-Weight Regression for {species_select}")
                    plt.legend()
                    st.pyplot(plt)
                else:
                    st.error("Insufficient data for regression (need at least 2 data points).")

            # Comments Section (Optional)
            comments = st.text_area("Add Comments (Optional):")
            if comments:
                st.write("### Comments")
                st.write(comments)

            # Export Report (HTML and PDF)
            if st.button("Export Report as HTML"):
                html_content = f"""
                <h1>Monitoring Report (Red Fleet Reservoir)</h1>
                <p><strong>Water:</strong> Red Fleet Reservoir</p>
                <p><strong>Date(s):</strong> {pd.to_datetime(df['Date'].min()).strftime('%m/%d/%Y')}-{pd.to_datetime(df['Date'].max()).strftime('%m/%d/%Y')}</p>
                <p><strong>Stocking Strategy:</strong> Not specified (assumed predator management and forage enhancement)</p>
                <p><strong>Target Species:</strong> {', '.join(abundance_df['Target Species'].unique())}</p>
                <p><strong>Methods Description:</strong> Electrofishing conducted over multiple transects, total effort {effort} hours.</p>
                <h3>Gear/Effort</h3>
                <table border="1">
                    <tr><th>Gear Type</th><th>Effort</th><th>Water Temp (°F)</th><th>Additional Data</th></tr>
                    <tr><td>Electrofishing</td><td>{effort} Hr.</td><td>{df[temp_column].mean().round(1)}</td><td>Diet (some species), length, weight</td></tr>
                </table>
                {abundance_df.to_html(index=False)}
                {catch_df.to_html(index=False)}
                {water_quality.to_frame().T.to_html(index=False) if 'Water Quality' in locals() else ''}
                {f'<h3>Comments</h3><p>{comments}</p>' if comments else ''}
                """
                st.download_button("Download HTML Report", html_content, "monitoring_report.html", "text/html")

            if st.button("Export Report as PDF"):
                html_content = f"""
                <h1>Monitoring Report (Red Fleet Reservoir)</h1>
                <p><strong>Water:</strong> Red Fleet Reservoir</p>
                <p><strong>Date(s):</strong> {pd.to_datetime(df['Date'].min()).strftime('%m/%d/%Y')}-{pd.to_datetime(df['Date'].max()).strftime('%m/%d/%Y')}</p>
                <p><strong>Stocking Strategy:</strong> Not specified (assumed predator management and forage enhancement)</p>
                <p><strong>Target Species:</strong> {', '.join(abundance_df['Target Species'].unique())}</p>
                <p><strong>Methods Description:</strong> Electrofishing conducted over multiple transects, total effort {effort} hours.</p>
                <h3>Gear/Effort</h3>
                <table border="1">
                    <tr><th>Gear Type</th><th>Effort</th><th>Water Temp (°F)</th><th>Additional Data</th></tr>
                    <tr><td>Electrofishing</td><td>{effort} Hr.</td><td>{df[temp_column].mean().round(1)}</td><td>Diet (some species), length, weight</td></tr>
                </table>
                {abundance_df.to_html(index=False)}
                {catch_df.to_html(index=False)}
                {water_quality.to_frame().T.to_html(index=False) if 'Water Quality' in locals() else ''}
                {f'<h3>Comments</h3><p>{comments}</p>' if comments else ''}
                """
                pdf(html_content, "monitoring_report.pdf")

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

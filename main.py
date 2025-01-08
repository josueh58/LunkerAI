import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# App Title
st.title("LunkerAI: Fisheries Data Analysis")
st.subheader("CPUE Calculator, Species Abundance, and Length Frequency Histogram")

# Standard Weight Formula Parameters
species_ws_params = {
    "Walleye": (-5.386, 3.230, 150),
    "Smallmouth Bass": (-5.329, 3.200, 150),
    "Largemouth Bass": (-5.528, 3.273, 150),
    "Bluegill": (-5.374, 3.316, 80),
    "Black Crappie": (-5.618, 3.345, 100),
    "Yellow Perch": (-5.210, 3.169, 100),
    "Brown Trout": (-5.230, 3.140, 120),
    "Rainbow Trout": (-5.186, 3.103, 120),
    "Brook Trout": (-5.189, 3.099, 100)
}


# Function to calculate standard weight (Ws)
def calculate_standard_weight(species, length):
    if species in species_ws_params and length >= species_ws_params[species][2]:
        a, b, min_tl = species_ws_params[species]
        return 10 ** (a + b * np.log10(length))
    return np.nan  # Return NaN if species not found or length below minimum


# File Upload
uploaded_file = st.file_uploader("Upload Fisheries Data (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("### Uploaded Data:")
    st.dataframe(df.head())

    # Select relevant columns
    species_column = st.selectbox("Select Species Column:", df.columns)
    effort_column = st.selectbox("Select Effort Column:", df.columns)
    length_column = st.selectbox("Select Fish Length Column (mm):", df.columns)
    weight_column = st.selectbox("Select Fish Weight Column:", df.columns)
    net_id_column = st.selectbox("Select Net ID Column:", df.columns)

    # Automatically compute total effort as the sum of unique net efforts
    effort_total = df.groupby(net_id_column)[effort_column].first().sum()

    # Calculate Standard Weight and Relative Weight
    df["Standard Weight"] = df.apply(lambda row: calculate_standard_weight(row[species_column], row[length_column]),
                                     axis=1)
    df["Relative Weight"] = df[weight_column] / df["Standard Weight"] * 100

    # CPUE Calculation (Effort summed per unique Net ID)
    if st.button("Calculate CPUE"):
        species_counts = df[species_column].value_counts().reset_index()
        species_counts.columns = ["Species", "Fish Count"]
        species_counts["CPUE Fish/Hr"] = species_counts["Fish Count"] / effort_total
        st.write("### CPUE Results:")
        st.dataframe(species_counts)

    # Species Abundance Table
    if st.button("Calculate Species Abundance"):
        total_fish = len(df)
        species_abundance = df.groupby(species_column).agg(
            CPUE_Fish_Hr=(species_column, 'count'),
            Mean_TL_inches=(length_column, lambda x: round(x.mean() / 25.4, 2)),
            Mean_TL=(length_column, 'mean'),
            Range_TL=(length_column, lambda x: f"{x.min()}-{x.max()}"),
            Mean_WT=(weight_column, 'mean'),
            Range_WT=(weight_column, lambda x: f"{x.min()}-{x.max()}"),
            Mean_Wr=("Relative Weight", 'mean')
        ).reset_index()
        species_abundance["CPUE Fish/Hr"] = species_abundance["CPUE_Fish_Hr"] / effort_total
        species_abundance = species_abundance.drop(columns=["CPUE_Fish_Hr"])
        species_abundance = species_abundance.sort_values(by="CPUE Fish/Hr", ascending=False)
        st.write("### Species Abundance:")
        st.dataframe(species_abundance)

    # Length Frequency Histogram
    if st.button("Generate Length Frequency Histogram"):
        plt.figure(figsize=(8, 5))
        plt.hist(df[length_column], bins=20, color='blue', edgecolor='black')
        plt.xlabel("Fish Length (mm)")
        plt.ylabel("Frequency")
        plt.title("Length Frequency Distribution")
        st.pyplot(plt)

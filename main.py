import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# App Title
st.title("LunkerAI: Fisheries Data Analysis")
st.subheader("CPUE Calculator, Species Abundance, and Length Frequency Histogram")

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

    # CPUE Calculation (Effort summed per unique Net ID)
    if st.button("Calculate CPUE"):
        effort_total = df[[net_id_column, effort_column]].drop_duplicates()[effort_column].sum()
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
            Mean_Wr=(weight_column, lambda x: round((x.mean() / x.median()) * 100, 2))
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


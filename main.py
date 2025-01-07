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

    # Select species column
    species_column = st.selectbox("Select Species Column:", df.columns)
    effort_column = st.selectbox("Select Effort Column:", df.columns)
    count_column = st.selectbox("Select Fish Count Column:", df.columns)
    length_column = st.selectbox("Select Fish Length Column (mm):", df.columns)

    # CPUE Calculation
    if st.button("Calculate CPUE"):
        df_cpue = df.groupby(species_column).apply(
            lambda x: x[count_column].sum() / x[effort_column].sum()).reset_index()
        df_cpue.columns = ["Species", "CPUE"]
        st.write("### CPUE Results:")
        st.dataframe(df_cpue)

    # Species Abundance
    if st.button("Calculate Species Abundance"):
        species_counts = df[species_column].value_counts().reset_index()
        species_counts.columns = ["Species", "Count"]
        st.write("### Species Abundance:")
        st.dataframe(species_counts)

    # Length Frequency Histogram
    if st.button("Generate Length Frequency Histogram"):
        plt.figure(figsize=(8, 5))
        plt.hist(df[length_column], bins=20, color='blue', edgecolor='black')
        plt.xlabel("Fish Length (mm)")
        plt.ylabel("Frequency")
        plt.title("Length Frequency Distribution")
        st.pyplot(plt)


import os
import sys
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import httpx
import chardet
import base64
from scipy.stats import ttest_ind
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Constants
AIPROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

if not AIPROXY_TOKEN:
    raise EnvironmentError("AIPROXY_TOKEN environment variable is not set.")

# Helper functions
def detect_encoding(filename: str) -> str:
    """Detect encoding of a file.

    Args:
        filename (str): Path to the file.

    Returns:
        str: Detected encoding of the file.
    """
    with open(filename, 'rb') as f:
        result = chardet.detect(f.read(10000))
        return result['encoding']

def load_csv(filename: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame with auto-detected encoding.

    Args:
        filename (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    try:
        encoding = detect_encoding(filename)
        if encoding.lower() == 'ascii':
            print(f"Detected 'ascii' encoding. Defaulting to 'utf-8'.")
            encoding = 'utf-8'

        df = pd.read_csv(filename, encoding=encoding, on_bad_lines='skip', encoding_errors='replace')
        print(f"Loaded {filename} with {df.shape[0]} rows and {df.shape[1]} columns using {encoding} encoding.")
        return df
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError while loading CSV: {e}. Retrying with 'ISO-8859-1' encoding.")
        try:
            df = pd.read_csv(filename, encoding='ISO-8859-1', on_bad_lines='skip', encoding_errors='replace')
            print(f"Successfully loaded {filename} with ISO-8859-1 encoding.")
            return df
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        sys.exit(1)

def analyze_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform basic and advanced analysis on the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to analyze.

    Returns:
        Dict[str, Any]: Dictionary containing analysis results, including summary statistics, 
                        missing values, correlation matrix, outliers, clustering, PCA results, 
                        and t-test results.
    """
    numeric_data = df.select_dtypes(include=[np.number])
    outliers = numeric_data[(np.abs(numeric_data - numeric_data.mean()) > (3 * numeric_data.std())).any(axis=1)]

    # Basic analysis
    analysis = {
        "summary_statistics": df.describe(include='all', percentiles=[.25, .5, .75]).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "correlation_matrix": df.corr(numeric_only=True).to_dict(),
        "outliers": outliers.to_dict(),
    }

    # Detect highly correlated features
    corr_matrix = numeric_data.corr()
    high_corr = [(col, corr_matrix[col][corr_matrix[col] > 0.8].index.tolist()) for col in corr_matrix.columns]
    analysis['high_correlation'] = high_corr

    # Hypothesis testing (e.g., t-tests for numeric columns)
    if len(numeric_data.columns) > 1:
        t_tests = {}
        columns = numeric_data.columns
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                t_stat, p_val = ttest_ind(numeric_data[columns[i]].dropna(), numeric_data[columns[j]].dropna())
                t_tests[f"{columns[i]} vs {columns[j]}"] = {"t_stat": t_stat, "p_val": p_val}
        analysis['t_tests'] = t_tests

    # Clustering analysis
    try:
        kmeans = KMeans(n_clusters=3, random_state=42).fit(numeric_data.dropna())
        analysis['clusters'] = kmeans.labels_.tolist()
    except Exception as e:
        print(f"Clustering failed: {e}")

    # PCA for dimensionality reduction
    try:
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(numeric_data.dropna())
        analysis['pca'] = {
            "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
            "components": pca.components_.tolist(),
            "transformed_data": pca_result.tolist()
        }
    except Exception as e:
        print(f"PCA failed: {e}")

    return analysis

def request_llm(prompt: str, functions: List[Dict[str, Any]] = None) -> str:
    """Send a request to the LLM with the given prompt and optional functions for function-calling.

    Args:
        prompt (str): Input prompt for the LLM.
        functions (List[Dict[str, Any]], optional): Optional function schema for enabling function-calling. Defaults to None.

    Returns:
        str: Response from the LLM.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    if functions:
        payload["functions"] = functions

    try:
        response = httpx.post(AIPROXY_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return ""

def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to a base64 string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def generate_narrative_with_visuals(analysis: Dict[str, Any], dataset_name: str, chart_paths: List[str]) -> str:
    """Use LLM to generate a narrative that includes insights from visualizations."""
    # Embed visualizations in the prompt as base64 strings
    chart_data = []
    for path in chart_paths:
        try:
            encoded_chart = encode_image_to_base64(path)
            chart_data.append({"name": os.path.basename(path), "image_base64": encoded_chart})
        except Exception as e:
            print(f"Failed to encode chart {path}: {e}")

    # Update the prompt
    prompt = (
        f"You are an expert data analyst with visual analysis capabilities. Analyze the following dataset "
        f"and visualizations for insights:\n\n"
        f"Dataset Name: {dataset_name}\n\n"
        f"Summary Statistics: {analysis['summary_statistics']}\n"
        f"Missing Values: {analysis['missing_values']}\n"
        f"High Correlations: {analysis['high_correlation']}\n"
        f"T-Tests Results: {analysis.get('t_tests', 'No t-tests were performed.')}\n"
        f"PCA Results: {analysis.get('pca', 'No PCA information available.')}\n\n"
        f"Visualizations (base64 encoded):\n"
        f"{chart_data}\n"
    )
    return request_llm(prompt)

def refine_analysis_with_llm(df: pd.DataFrame, initial_analysis: Dict[str, Any], dataset_name: str) -> Dict[str, Any]:
    """Iteratively refine analysis based on LLM feedback."""
    analysis = initial_analysis
    feedback = generate_narrative_with_visuals(analysis, dataset_name, [])
    print(f"LLM Feedback:\n{feedback}")

    for iteration in range(3):  # Limit to 3 iterations
        print(f"Refinement Iteration {iteration + 1}:")

        # Simulate refinement process based on feedback
        if "focus on missing values" in feedback.lower():
            print("Refining analysis to handle missing values...")
            analysis['missing_values'] = df.fillna(df.mean()).isnull().sum().to_dict()

        elif "improve clustering" in feedback.lower():
            print("Refining clustering analysis...")
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df.select_dtypes(include=[np.number]).dropna())
            kmeans = KMeans(n_clusters=4, random_state=42).fit(scaled_data)
            analysis['clusters'] = kmeans.labels_.tolist()

        elif "more visualizations" in feedback.lower():
            print("Generating additional visualizations...")
            # Example: Generate histograms for numerical columns
            for col in df.select_dtypes(include=[np.number]).columns:
                plt.figure()
                df[col].hist(bins=20, edgecolor='black')
                plt.title(f"Histogram of {col}")
                plt.xlabel(col)
                plt.ylabel("Frequency")
                plt.savefig(f"{dataset_name}_histogram_{col}.png")
                plt.close()

            # Example: Generate scatter plots for the first two numerical columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                plt.figure()
                plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.6)
                plt.title(f"Scatter Plot: {numeric_cols[0]} vs {numeric_cols[1]}")
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
                plt.savefig(f"{dataset_name}_scatter_{numeric_cols[0]}_vs_{numeric_cols[1]}.png")
                plt.close()

            # Example: Pair plot using seaborn for smaller datasets
            if df.shape[0] <= 1000:  # Limit size for pair plot
                sns.pairplot(df.select_dtypes(include=[np.number]))
                plt.savefig(f"{dataset_name}_pairplot.png")
                plt.close()

        feedback = request_llm(f"Updated analysis:\n{analysis}")

    return analysis

def visualize_data(df: pd.DataFrame, folder_name: str) -> List[str]:
    """Generate and save visualizations of the data.

    Args:
        df (pd.DataFrame): DataFrame to visualize.
        folder_name (str): Folder to save generated charts.

    Returns:
        List[str]: List of paths to the generated chart files.
    """
    charts = []
    try:
        plt.figure(figsize=(10, 8))
        sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="coolwarm", fmt=".2f")
        chart_name = os.path.join(folder_name, "correlation_heatmap.png") 
        plt.title("Correlation Heatmap")
        plt.savefig(chart_name, dpi=300, bbox_inches='tight')
        charts.append(chart_name)
        plt.close()

        plt.figure(figsize=(10, 8))
        sns.heatmap(df.isnull(), cbar=False, cmap="viridis")
        plt.title("Missing Values Heatmap")
        chart_name = os.path.join(folder_name, "missing_values_heatmap.png")
        plt.savefig(chart_name, dpi=300, bbox_inches='tight')
        charts.append(chart_name)
        plt.close()

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for i, col in enumerate(numeric_cols[:5]):
            plt.figure(figsize=(8, 6))
            sns.histplot(df[col], kde=True, bins=30, color="blue", alpha=0.7)
            plt.title(f"Distribution of {col}")
            plt.xlabel(col)
            plt.ylabel("Frequency")
            chart_name = os.path.join(folder_name, f"distribution_{col}.png")
            plt.savefig(chart_name, dpi=300, bbox_inches='tight')
            charts.append(chart_name)
            plt.close()

        if len(numeric_cols) > 1:
            sns.pairplot(df[numeric_cols[:5]])
            chart_name = os.path.join(folder_name, "pairplot.png")
            plt.savefig(chart_name, dpi=300, bbox_inches='tight')
            charts.append(chart_name)
            plt.close()
    except Exception as e:
        print(f"Error generating visualizations: {e}")

    return charts

def create_readme(analysis: Dict[str, Any], narrative: str, charts: List[str], df_name: str, folder_name: str):
    """Generate a README.md file summarizing the analysis and visualizations.

    Args:
        analysis (Dict[str, Any]): Analysis results.
        narrative (str): Generated narrative for the dataset.
        charts (List[str]): List of chart file paths.
        df_name (str): Dataset name.
        folder_name (str): Folder to save the README.
    """
    readme_path = os.path.join(folder_name, "README.md")
    readme_content = f"""# Automated Data Analysis Report

## Dataset: {df_name}

### Overview
This analysis was automatically generated using the Autolysis script. Below is a summary of the dataset, analysis, and insights.

### Dataset Information
- **Columns**: {len(analysis['data_types'])}
- **Rows**: {len(analysis['summary_statistics'])}
- **Column Data Types**: {analysis['data_types']}

### Key Findings
- **Summary Statistics**:
{pd.DataFrame(analysis['summary_statistics']).to_string()}

- **Missing Values**:
{pd.Series(analysis['missing_values']).to_string()}

### Narrative
{narrative}

### Visualizations
"""

    for i, chart in enumerate(charts):
        readme_content += f"- ![Chart {i + 1}](./{os.path.basename(chart)})\n"

    with open(readme_path, "w") as f:
        f.write(readme_content)

    print(f"README.md created at {readme_path}.")

def main():
    """Main entry point of the script with LLM-driven iterative refinement."""
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)

    csv_filename = sys.argv[1]
    folder_name = os.path.splitext(os.path.basename(csv_filename))[0]
    os.makedirs(folder_name, exist_ok=True)

    # Step 1: Load the dataset
    df = load_csv(csv_filename)

    # Step 2: Perform initial analysis
    initial_analysis = analyze_data(df)

    # Step 3: Generate initial visualizations
    charts = visualize_data(df, folder_name)

    # Step 4: Iteratively refine analysis and visualizations
    refined_analysis = refine_analysis_with_llm(df, initial_analysis, csv_filename)

    # Step 5: Generate final narrative
    narrative = generate_narrative_with_visuals(refined_analysis, csv_filename, charts)

    # Step 6: Create README report
    create_readme(refined_analysis, narrative, charts, csv_filename, folder_name)

    print("Analysis complete with iterative refinement.")

if __name__ == "__main__":
    main()

#$env:AIPROXY_TOKEN="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDAzMTNAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.WUELtGa5HIUynQp5apYXd0gafro7uqeCUxvdRAIOztk"
# Automated Data Analysis Report

## Dataset: media.csv

### Overview
This analysis was automatically generated using the Autolysis script. Below is a summary of the dataset, analysis, and insights.

### Dataset Information
- **Columns**: 8
- **Rows**: 9 (approximate)
- **Column Data Types**:
- date: object
- language: object
- type: object
- title: object
- by: object
- overall: int64
- quality: int64
- repeatability: int64


### Key Findings
#### Summary Statistics
| index         |   count |   unique | top               |   freq |      mean |        std |   min |   25% |   50% |   75% |   max |
|:--------------|--------:|---------:|:------------------|-------:|----------:|-----------:|------:|------:|------:|------:|------:|
| date          |    2553 |     2055 | 21-May-06         |      8 | nan       | nan        |   nan |   nan |   nan |   nan |   nan |
| language      |    2652 |       11 | English           |   1306 | nan       | nan        |   nan |   nan |   nan |   nan |   nan |
| type          |    2652 |        8 | movie             |   2211 | nan       | nan        |   nan |   nan |   nan |   nan |   nan |
| title         |    2652 |     2312 | Kanda Naal Mudhal |      9 | nan       | nan        |   nan |   nan |   nan |   nan |   nan |
| by            |    2390 |     1528 | Kiefer Sutherland |     48 | nan       | nan        |   nan |   nan |   nan |   nan |   nan |
| overall       |    2652 |      nan | nan               |    nan |   3.04751 |   0.76218  |     1 |     3 |     3 |     3 |     5 |
| quality       |    2652 |      nan | nan               |    nan |   3.20928 |   0.796743 |     1 |     3 |     3 |     4 |     5 |
| repeatability |    2652 |      nan | nan               |    nan |   1.49472 |   0.598289 |     1 |     1 |     1 |     2 |     3 |

#### Missing Values
|               |   Missing Values |
|:--------------|-----------------:|
| date          |               99 |
| language      |                0 |
| type          |                0 |
| title         |                0 |
| by            |              262 |
| overall       |                0 |
| quality       |                0 |
| repeatability |                0 |

### Narrative


### Visualizations
- Chart 1: ![Chart 1](./correlation_heatmap.png)
- Chart 2: ![Chart 2](./missing_values_heatmap.png)
- Chart 3: ![Chart 3](./distribution_overall.png)
- Chart 4: ![Chart 4](./distribution_quality.png)
- Chart 5: ![Chart 5](./distribution_repeatability.png)
- Chart 6: ![Chart 6](./pairplot.png)

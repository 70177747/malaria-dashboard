"""Chart helper file required by the project structure. Main dashboard uses Plotly for interaction and imports Matplotlib/Seaborn as required by the assignment."""
import matplotlib.pyplot as plt
import seaborn as sns

def apply_seaborn_theme():
    sns.set_theme(style="whitegrid")
    return plt

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json

def create_graph(path: str):
    """Create a graph of the accuracy, CER, and WER per evaluated model.

    Args:
        path (str): Path to the JSON file containing the data.
    """
    with open(f"{path}", "r") as f:
        data = json.load(f)

    df = pd.DataFrame.from_dict(data, orient="index").reset_index()
    df.rename(columns={"index": "model"}, inplace=True)

    model_order = df.sort_values("avg_accuracy", ascending=False)["model"]

    df_cer_wer = df[["model", "avg_cer", "avg_wer"]].melt(
        id_vars="model", var_name="metric", value_name="value"
    )

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 6))

    # --- Plot 1: Accuracy ---
    ax1 = axes[0]
    sns.barplot(
        ax=axes[0],
        data=df,
        y="model",
        x="avg_accuracy",
        order=model_order,
        hue="avg_accuracy",
        palette="flare",
        dodge=False,
        legend=False
    )
    ax1.set_title("Average Accuracy per Model")
    ax1.set_xlabel("Accuracy (%)")
    ax1.set_ylabel("")
    ax1.set_xlim(80, 100)
    ax1.set_xticks(range(80, 101, 5))
    
    for container in ax1.containers:
        ax1.bar_label(container, fmt="%.2f", padding=3)

    # --- Plot 2: CER and WER ---
    ax2 = axes[1]
    sns.barplot(
        ax=axes[1],
        data=df_cer_wer,
        y="model",
        x="value",
        hue="metric",
        order=model_order,
        palette="mako"
    )
    ax2.set_title("CER vs WER per Model")
    ax2.set_xlabel("Error Rate (%)")
    ax2.set_ylabel("")
    ax2.set_xlim(0, 100)
    ax2.set_xticks(range(0, 101, 10))
    ax2.legend(title="Metrics")
    
    for container in ax2.containers:
        ax2.bar_label(container, fmt="%.2f", padding=3)

    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{path}.png")


if  __name__ == "__main__":
    create_graph("docs/json/GT4HistOCR/corpus/EarlyModernLatin/1564-Thucydides-Valla.json")
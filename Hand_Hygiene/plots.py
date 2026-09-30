import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_data(filename='hand_hygiene_activities.csv'):
    try:
        df = pd.read_csv(filename)
        return df
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please make sure the file is in the current directory.")
        return None

def prepare_data(df):
    df.columns = df.columns.str.strip()
    
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    
    df['duration_seconds'] = (df['end_time'] - df['start_time']).dt.total_seconds()
    
    return df

def calculate_case_averages(df):
    case_totals = df.groupby(['filename_base', 'log_type'])['ml_used'].sum().reset_index()
    case_averages = case_totals.groupby('log_type')['ml_used'].apply(list).reset_index()
    
    return case_averages

def calculate_activity_averages(df):
    activity_data = df.groupby('log_type')['ml_used'].apply(list).reset_index()
    
    return activity_data

def create_box_plots(df):    
    case_data = calculate_case_averages(df)
    activity_data = calculate_activity_averages(df)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
    
    log_types = case_data['log_type'].unique()
    case_plot_data = []
    case_labels = []
    
    for log_type in log_types:
        data = case_data[case_data['log_type'] == log_type]['ml_used'].iloc[0]
        case_plot_data.append(data)
        case_labels.append(log_type)
    
    overall_case_data = df.groupby('filename_base')['ml_used'].sum().tolist()
    case_plot_data.append(overall_case_data)
    case_labels.append('Overall')
    
    bp1 = ax1.boxplot(case_plot_data, labels=case_labels, patch_artist=True)
    ax1.set_title('ML Used per Case (Summed)\nGrouped by Log Type', fontsize=12, fontweight='bold')
    ax1.set_ylabel('ML Used', fontsize=10)
    ax1.set_xlabel('Log Type', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']
    for patch, color in zip(bp1['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    activity_plot_data = []
    activity_labels = []
    
    for log_type in log_types:
        data = activity_data[activity_data['log_type'] == log_type]['ml_used'].iloc[0]
        activity_plot_data.append(data)
        activity_labels.append(log_type)
    
    overall_activity_data = df['ml_used'].tolist()
    activity_plot_data.append(overall_activity_data)
    activity_labels.append('overall')
    
    bp2 = ax2.boxplot(activity_plot_data, labels=activity_labels, patch_artist=True)
    ax2.set_title('ML Used per Individual Activity Instance\nGrouped by Log Type', fontsize=12, fontweight='bold')
    ax2.set_ylabel('ML Used', fontsize=10)
    ax2.set_xlabel('Log Type', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    for patch, color in zip(bp2['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.tight_layout()
    
    return fig

def print_summary_statistics(df):
    print("Dataset Summary:")
    print(f"Total records: {len(df)}")
    print(f"Date range: {df['start_time'].min()} to {df['start_time'].max()}")
    print(f"Log types: {df['log_type'].unique()}")
    print(f"Unique cases (filename_base): {df['filename_base'].nunique()}")
    print()
    
    print("Summary by Log Type:")
    for log_type in df['log_type'].unique():
        subset = df[df['log_type'] == log_type]
        print(f"\n{log_type.upper()}:")
        print(f"  Activities: {len(subset)}")
        print(f"  Cases: {subset['filename_base'].nunique()}")
        print(f"  Total ML used: {subset['ml_used'].sum():.1f}")
        print(f"  Average ML per activity: {subset['ml_used'].mean():.2f}")
        print(f"  Average ML per case: {subset.groupby('filename_base')['ml_used'].sum().mean():.2f}")
    
    print(f"\nOVERALL:")
    print(f"  Activities: {len(df)}")
    print(f"  Cases: {df['filename_base'].nunique()}")
    print(f"  Total ML used: {df['ml_used'].sum():.1f}")
    print(f"  Average ML per activity: {df['ml_used'].mean():.2f}")
    print(f"  Average ML per case: {df.groupby('filename_base')['ml_used'].sum().mean():.2f}")

def main():
    df = load_data()
    if df is None:
        return
    
    df = prepare_data(df)
    print_summary_statistics(df)
    fig = create_box_plots(df)
    plt.show()
    
    plt.savefig('hand_hygiene_analysis.png', dpi=300, bbox_inches='tight')
    print("\nPlots saved as 'hand_hygiene_analysis.png'")

if __name__ == "__main__":
    main()
import pandas as pd
import numpy as np
import json
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

def calculate_statistics(data):
    if len(data) == 0:
        return {
            'count': 0,
            'mean': None,
            'median': None,
            'q1': None,
            'q3': None,
            'min': None,
            'max': None,
            'std': None
        }
    
    return {
        'count': len(data),
        'mean': float(np.mean(data)),
        'median': float(np.median(data)),
        'q1': float(np.percentile(data, 25)),
        'q3': float(np.percentile(data, 75)),
        'min': float(np.min(data)),
        'max': float(np.max(data)),
        'std': float(np.std(data))
    }

def calculate_case_statistics(df):
    case_totals = df.groupby(['filename_base', 'log_type'])['ml_used'].sum().reset_index()
    
    case_stats = {}
    
    for log_type in df['log_type'].unique():
        log_data = case_totals[case_totals['log_type'] == log_type]['ml_used'].tolist()
        case_stats[log_type] = calculate_statistics(log_data)
    
    overall_case_totals = df.groupby('filename_base')['ml_used'].sum().tolist()
    case_stats['overall'] = calculate_statistics(overall_case_totals)
    
    return case_stats

def calculate_activity_statistics(df):
    activity_stats = {}
    
    for log_type in df['log_type'].unique():
        log_data = df[df['log_type'] == log_type]['ml_used'].tolist()
        activity_stats[log_type] = calculate_statistics(log_data)
    
    overall_activity_data = df['ml_used'].tolist()
    activity_stats['overall'] = calculate_statistics(overall_activity_data)
    
    return activity_stats

def create_comprehensive_statistics(df):
    stats = {
        'metadata': {
            'total_records': len(df),
            'date_range': {
                'start': df['start_time'].min().isoformat(),
                'end': df['start_time'].max().isoformat()
            },
            'log_types': sorted(df['log_type'].unique().tolist()),
            'unique_cases': df['filename_base'].nunique(),
            'generated_timestamp': pd.Timestamp.now().isoformat()
        },
        'case_statistics': {
            'description': 'Statistics for ml_used summed per case (filename_base)',
            'data': calculate_case_statistics(df)
        },
        'activity_statistics': {
            'description': 'Statistics for ml_used per individual activity instance',
            'data': calculate_activity_statistics(df)
        }
    }
    
    return stats

def save_statistics_json(stats, filename='hand_hygiene_statistics.json'):
    with open(filename, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to {filename}")

def print_summary_table(stats):
    print("\n" + "="*80)
    print("HAND HYGIENE STATISTICS SUMMARY")
    print("="*80)
    
    print(f"\nDataset Overview:")
    print(f"  Total Records: {stats['metadata']['total_records']}")
    print(f"  Unique Cases: {stats['metadata']['unique_cases']}")
    print(f"  Log Types: {', '.join(stats['metadata']['log_types'])}")
    print(f"  Date Range: {stats['metadata']['date_range']['start']} to {stats['metadata']['date_range']['end']}")
    
    print(f"\n{'CASE STATISTICS (ML Used per Case - Summed)':^80}")
    print("-"*80)
    print(f"{'Log Type':<15} {'Count':<8} {'Mean':<10} {'Median':<10} {'Q1':<10} {'Q3':<10} {'Min':<10} {'Max':<10}")
    print("-"*80)
    
    for log_type, data in stats['case_statistics']['data'].items():
        if data['count'] > 0:
            print(f"{log_type:<15} {data['count']:<8} {data['mean']:<10.2f} {data['median']:<10.2f} "
                  f"{data['q1']:<10.2f} {data['q3']:<10.2f} {data['min']:<10.2f} {data['max']:<10.2f}")
    
    print(f"\n{'ACTIVITY STATISTICS (ML Used per Individual Activity)':^80}")
    print("-"*80)
    print(f"{'Log Type':<15} {'Count':<8} {'Mean':<10} {'Median':<10} {'Q1':<10} {'Q3':<10} {'Min':<10} {'Max':<10}")
    print("-"*80)
    
    for log_type, data in stats['activity_statistics']['data'].items():
        if data['count'] > 0:
            print(f"{log_type:<15} {data['count']:<8} {data['mean']:<10.2f} {data['median']:<10.2f} "
                  f"{data['q1']:<10.2f} {data['q3']:<10.2f} {data['min']:<10.2f} {data['max']:<10.2f}")

def main():
    df = load_data()
    if df is None:
        return
    
    df = prepare_data(df)
    
    stats = create_comprehensive_statistics(df)
    
    save_statistics_json(stats)
    
    print_summary_table(stats)
    
    print(f"\nDetailed statistics saved to 'hand_hygiene_statistics.json'")

if __name__ == "__main__":
    main()
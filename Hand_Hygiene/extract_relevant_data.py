import pandas as pd
import os
import pm4py
from datetime import timedelta

hand_hygiene_activities = []

for filename in os.listdir('gt'):
    base_filename = filename.split(".")[0]
    gt_filename = base_filename + ".xes"
    iot_filename = base_filename + ".jsonl"
    
    print("Processing files: ", gt_filename, " and ", iot_filename)
    
    df = pd.read_json(os.path.join("iot", iot_filename), lines=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)  # Force UTC timezone
    df.set_index('timestamp', inplace=True)
    
    gt_filepath = os.path.join("gt", gt_filename)
    log_df = pm4py.read_xes(gt_filepath)
    log_df = log_df.sort_values("time:timestamp")
    
    log_df['time:timestamp'] = pd.to_datetime(log_df['time:timestamp'], utc=True)
    
    log_type = "basic"
    
    if any(str(name).lower() == "disturbance" for name in log_df["concept:name"]):
        log_type = "disturbance"
    elif "case:concept:name" in log_df.columns and any(str(case).lower() == "patient right" for case in log_df["case:concept:name"]):
        log_type = "two_patients"
    
    print(f"Log type for {base_filename}: {log_type}")
    
    hh_temp = {}
    
    for _, event in log_df.iterrows():
        name = event["concept:name"]
        transition = event["lifecycle:transition"]
        instance_id = event["concept:instance"]
        timestamp = event["time:timestamp"]
        
        if "hand hygiene" in str(name).lower():
            if transition == "start":
                hh_temp[instance_id] = timestamp
            elif transition == "complete" and instance_id in hh_temp:
                start_time = hh_temp.pop(instance_id)
                end_time = timestamp
                hand_hygiene_activities.append({
                    "filename_base": base_filename,
                    "log_type": log_type,
                    "start_time": start_time,
                    "end_time": end_time
                })
    
    hygiene_df = df[df["station"] == "HYGIENE_STATION"]
    
    for activity in hand_hygiene_activities:
        if activity["filename_base"] != base_filename:
            continue 
        
        start_target = activity["start_time"] - timedelta(seconds=3)
        end_target = activity["end_time"] + timedelta(seconds=3)
        
        indexer = hygiene_df.index.get_indexer([start_target], method='nearest')
        if indexer[0] != -1:
            activity["s23xq_weight_before_start"] = hygiene_df.iloc[indexer[0]]["s23xq_load_cell_weight"]
        else:
            activity["s23xq_weight_before_start"] = None
        
        indexer = hygiene_df.index.get_indexer([end_target], method='nearest')
        if indexer[0] != -1:
            activity["s23xq_weight_after_end"] = hygiene_df.iloc[indexer[0]]["s23xq_load_cell_weight"]
        else:
            activity["s23xq_weight_after_end"] = None
        
        if activity["s23xq_weight_before_start"] is not None and activity["s23xq_weight_after_end"] is not None:
            activity["ml_used"] = activity["s23xq_weight_before_start"] - activity["s23xq_weight_after_end"]
        else:
            activity["ml_used"] = None

for activity in hand_hygiene_activities:
    print(activity)

if hand_hygiene_activities:
    activities_df = pd.DataFrame(hand_hygiene_activities)
    activities_df.to_csv('hand_hygiene_activities.csv', index=False)
    print(f"\nData exported to 'hand_hygiene_activities.csv' with {len(hand_hygiene_activities)} activities")
else:
    print("\nNo hand hygiene activities found to export")
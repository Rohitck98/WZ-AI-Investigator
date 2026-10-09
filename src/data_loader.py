from __future__ import annotations
import re
import pandas as pd

def clean_name(name: str) -> str:
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return name

def first_existing(columns, candidates):
    for c in candidates:
        if c in columns:
            return c
    return None

def load_workzones(source):
    df = pd.read_csv(source)

    df.columns = [clean_name(c) for c in df.columns]

    
    df = df.dropna(how="all").drop_duplicates().reset_index(drop=True)
    df.insert(0, "record_id", range(1, len(df)+1))

    aliases = {
    "road": [
        "road_names",
        "road",
        "road_name",
        "roadway",
        "route",
        "street",
    ],

    "direction": [
        "direction",
        "dir",
        "travel_direction",
    ],

    "start": [
        "start_date_only",
        "start_date",
        "begin_date",
        "start",
        "from_date",
    ],

    "end": [
        "end_date_only",
        "end_date",
        "finish_date",
        "end",
        "to_date",
    ],

    "impact": [
        "work_zone_impact",
        "impact",
        "closure_type",
    ],

    "description": [
        "description",
        "work_description",
        "details",
        "name",
    ],

    "project": [
        "project_name",
        "project",
        "name",
    ],
}
    schema = {k: first_existing(df.columns, v) for k,v in aliases.items()}
    for key in ("start", "end"):
        col=schema[key]
        if col:
            df[col]=pd.to_datetime(df[col], errors="coerce")
    if schema["start"] and schema["end"]:
        df["duration_days"]=(df[schema["end"]]-df[schema["start"]]).dt.days+1
    return df, schema

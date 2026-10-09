from __future__ import annotations
import re
import pandas as pd
from dateutil import parser

def _contains(series, value):
    return series.fillna("").astype(str).str.contains(re.escape(value), case=False, na=False)

def _extract_date(question):
    patterns=[r"\b\d{4}-\d{1,2}-\d{1,2}\b", r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,\s*\d{4})?\b"]
    for p in patterns:
        m=re.search(p, question, re.I)
        if m:
            try: return pd.Timestamp(parser.parse(m.group(0), fuzzy=False).date())
            except Exception: pass
    return None

def answer_question(df, schema, question):
    q=question.strip().lower()
    result=df.copy()
    filters=[]

    if "how many" in q or "count" in q:
        mode="count"
    else:
        mode="rows"

    direction_map={"northbound":"northbound", "southbound":"southbound", "eastbound":"eastbound", "westbound":"westbound", " nb ":"northbound", " sb ":"southbound", " eb ":"eastbound", " wb ":"westbound"}
    if schema.get("direction"):
        padded=f" {q} "
        for token,value in direction_map.items():
            if token in padded:
                result=result[_contains(result[schema["direction"]], value)]
                filters.append(f"Direction contains '{value}'")
                break

    date=_extract_date(question)
    if date is not None and schema.get("start") and schema.get("end"):
        result=result[(result[schema["start"]].dt.normalize() <= date) & (result[schema["end"]].dt.normalize() >= date)]
        filters.append(f"Active on {date.date()}")

    if schema.get("impact"):
        if "full closure" in q or "all lanes closed" in q:
            result=result[_contains(result[schema["impact"]], "all") | _contains(result[schema["impact"]], "full")]
            filters.append("Full/all-lane closure")
        elif "partial closure" in q or "some lanes" in q:
            result=result[_contains(result[schema["impact"]], "some") | _contains(result[schema["impact"]], "partial")]
            filters.append("Partial/some-lane closure")

    if ("which road" in q or "most work zones" in q) and schema.get("road"):
        counts=result[schema["road"]].fillna("Unknown").value_counts().rename_axis("road").reset_index(name="work_zone_count")
        return f"The leading roadway is **{counts.iloc[0]['road']}** with **{counts.iloc[0]['work_zone_count']}** records." if len(counts) else "No matching records.", counts, filters or ["Grouped by roadway"]

    searchable_words=[]
    road_col=schema.get("road")
    if road_col:
        roads=sorted(df[road_col].dropna().astype(str).unique(), key=len, reverse=True)
        for road in roads:
            if road.lower() in q:
                result=result[_contains(result[road_col], road)]
                filters.append(f"Road contains '{road}'")
                break

    if not filters:
        stop={"show","find","work","zone","zones","all","the","on","in","for","me","which","are","there","active","how","many","with"}
        searchable_words=[w for w in re.findall(r"[a-z0-9-]+", q) if len(w)>2 and w not in stop]
        text_cols=[c for c in [schema.get("description"),schema.get("project"),schema.get("road")] if c]
        if searchable_words and text_cols:
            mask=pd.Series(False,index=result.index)
            for word in searchable_words:
                for col in text_cols: mask |= _contains(result[col], word)
            result=result[mask]
            filters.append("Keyword search: "+", ".join(searchable_words))

    if mode=="count":
        return f"I found **{len(result)}** matching work-zone records.", result, filters or ["No filters"]
    return f"I found **{len(result)}** matching work-zone records.", result, filters or ["No filters"]

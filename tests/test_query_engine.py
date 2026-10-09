import pandas as pd
from src.query_engine import answer_question

def test_count_and_direction():
    df=pd.DataFrame({"direction":["Northbound","Southbound"],"road":["IH 35","IH 35"]})
    text,result,_=answer_question(df,{"direction":"direction","road":"road","start":None,"end":None,"impact":None,"description":None,"project":None},"How many northbound work zones?")
    assert len(result)==1
    assert "1" in text

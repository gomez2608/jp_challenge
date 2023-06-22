import spacy
from spacy import displacy
import pandas as pd
import datetime as dt
import requests
import json
from django.conf import settings


nlp = spacy.load("en_core_web_sm")


class Analyzer:
    def __init__(self,dataset_route) -> None:
        self.data = pd.read_csv(dataset_route,encoding="utf-8")

    def convert_to_dt(self,value):
        value = str(value)
        if "," in value:
            try:
                return dt.datetime.strptime(value,"%B %d, %Y")
            except:
                return dt.datetime.strptime(value,"%b %d, %Y")
        else:
            try:
                return dt.datetime.strptime(value,"%B %Y")
            except:
                return dt.datetime.strptime(value,"%b %Y")

    def get_best_team(self, entities = ()):
        ds = self.data
        dataset = ds.copy()
        dataset["Date"] = dataset["Date"].apply(lambda x:dt.datetime.strptime(x,"%b %d %Y"))
        if len(entities) > 0:
            entities = list(map(self.convert_to_dt,entities))
            if len(entities) > 1:
                dataset = dataset[(dataset["Date"] >= entities[0]) & (dataset["Date"] <= entities[1])]
            else:
                dataset = dataset[(dataset["Date"].dt.year == entities[0].year) & (dataset["Date"].dt.month == entities[0].month) & (dataset["Date"].dt.day == entities[0].day)]
                if len(dataset) <1:
                    return ("",0)
        matches_best_team = 0
        pos_best = []
        for each_team in dataset["Team 1"].unique():
            matches_local = dataset[(dataset["Team 1"] == each_team)]
            matches_visitor = dataset[(dataset["Team 2"] == each_team)]
            local_wins = len(matches_local[matches_local["FT"].apply(lambda x: float(x.split("-")[0])>float(x.split("-")[1]))])
            visit_wins = len(matches_visitor[matches_visitor["FT"].apply(lambda x: float(x.split("-")[0])<float(x.split("-")[1]))])
            won_matches = local_wins + visit_wins
            if won_matches > matches_best_team:
                matches_best_team = won_matches
        
        for each_team in dataset["Team 1"].unique():
            matches_local = dataset[(dataset["Team 1"] == each_team)]
            matches_visitor = dataset[(dataset["Team 2"] == each_team)]
            local_wins = len(matches_local[matches_local["FT"].apply(lambda x: float(x.split("-")[0])>float(x.split("-")[1]))])
            visit_wins = len(matches_visitor[matches_visitor["FT"].apply(lambda x: float(x.split("-")[0])<float(x.split("-")[1]))])
            won_matches = local_wins + visit_wins
            if won_matches == matches_best_team:
                pos_best.append(each_team)

        return pos_best,matches_best_team

    def get_worst_team(self, entities = None):
        ds = self.data
        dataset = ds.copy()
        dataset["Date"] = dataset["Date"].apply(lambda x:dt.datetime.strptime(x,"%b %d %Y"))
        if len(entities) > 0:
            entities = list(map(self.convert_to_dt,entities))
            if len(entities) > 1:
                dataset = dataset[(dataset["Date"] >= entities[0]) & (dataset["Date"] <= entities[1])]
            else:
                dataset = dataset[(dataset["Date"].dt.year == entities[0].year) & (dataset["Date"].dt.month == entities[0].month) & (dataset["Date"].dt.day == entities[0].day)]
                if len(dataset) <1:
                    return ("",0)
        matches_worst_team = 0
        pos_worst = []
        for each_team in dataset["Team 1"].unique():
            matches_local = dataset[(dataset["Team 1"] == each_team)]
            matches_visitor = dataset[(dataset["Team 2"] == each_team)]
            local_losses = len(matches_local[matches_local["FT"].apply(lambda x: float(x.split("-")[0])<float(x.split("-")[1]))])
            visit_losses = len(matches_visitor[matches_visitor["FT"].apply(lambda x: float(x.split("-")[0])>float(x.split("-")[1]))])
            lost_matches = local_losses + visit_losses
            if lost_matches > matches_worst_team:
                matches_worst_team = lost_matches
        
        for each_team in dataset["Team 1"].unique():
            matches_local = dataset[(dataset["Team 1"] == each_team)]
            matches_visitor = dataset[(dataset["Team 2"] == each_team)]
            local_losses = len(matches_local[matches_local["FT"].apply(lambda x: float(x.split("-")[0])<float(x.split("-")[1]))])
            visit_losses = len(matches_visitor[matches_visitor["FT"].apply(lambda x: float(x.split("-")[0])>float(x.split("-")[1]))])
            lost_matches = local_losses + visit_losses
            if lost_matches == matches_worst_team:
                pos_worst.append(each_team)

        return pos_worst,matches_worst_team
    
    def get_win_matches(self, team,entities = ()):
        ds = self.data
        dataset = ds.copy()
        dataset["Date"] = dataset["Date"].apply(lambda x:dt.datetime.strptime(x,"%b %d %Y"))
        if len(entities) > 0:
            entities = list(map(self.convert_to_dt,entities))
            if len(entities) > 1:
                dataset = dataset[(dataset["Date"] >= entities[0]) & (dataset["Date"] <= entities[1])]
            else:
                dataset = dataset[(dataset["Date"].dt.year == entities[0].year) & (dataset["Date"].dt.month == entities[0].month) & (dataset["Date"].dt.day == entities[0].day)]
                if len(dataset) <1:
                    return ("",0)
        
        matches_local = dataset[(dataset["Team 1"] == team)]
        matches_visitor = dataset[(dataset["Team 2"] == team)]
        local_winnings = len(matches_local[matches_local["FT"].apply(lambda x: float(x.split("-")[0])>float(x.split("-")[1]))])
        visit_winnings = len(matches_visitor[matches_visitor["FT"].apply(lambda x: float(x.split("-")[0])<float(x.split("-")[1]))])
        win_matches = local_winnings + visit_winnings
        return team, win_matches
        



class PromptProcessor(Analyzer):
    
    def __init__(self, dataset_route) -> None:
        super().__init__(dataset_route)

    
    def get_entities(self,prompt:str):
        doc = nlp(prompt)
        ent = [(w.text, w.pos_,w.tag_) for w in doc]
        dic_ent = {}
        for i in ent:
            dic_ent[i[1]] = dic_ent.get(i[1],[])
            dic_ent[i[1]].append(i[0])
        dic_ent["ENT"] = doc.ents 
        return dic_ent
    
    def get_answer(self,prompt):
        entit = self.get_entities(prompt)
        print(entit)
        
        if "best" in entit["ADJ"] or "win" in entit["NOUN"]:
            if entit["ENT"] == None:
                return self.get_best_team()
            else:
                return self.get_best_team(entit["ENT"])
        
        elif "worst" in entit["ADJ"] or "lost" in entit["NOUN"]:
            if entit["ENT"] == None:
                return self.get_worst_team()
            else:
                return self.get_worst_team(entit["ENT"])
        elif "how" in entit["NOUN"] and "lost" in entit["NOUN"]:
            if entit["ENT"] == None:
                return self.get_win_matches()
            else:
                return self.get_win_matches(entit["ENT"])
    
class ResponseGenerator(PromptProcessor):

    def __init__(self, dataset_route) -> None:
        super().__init__(dataset_route)

    url = "https://api.ai21.com/studio/v1/j2-mid/complete"

    payload = {
        "numResults": 1,
        "maxTokens": 100,
        "minTokens": 0,
        "temperature": 0.7,
        "topP": 1,
        "topKReturn": 0,
        "frequencyPenalty": {
            "scale": 1,
            "applyToWhitespaces": True,
            "applyToPunctuations": True,
            "applyToNumbers": True,
            "applyToStopwords": True,
            "applyToEmojis": True
        },
        "presencePenalty": {
            "scale": 0,
            "applyToWhitespaces": True,
            "applyToPunctuations": True,
            "applyToNumbers": True,
            "applyToStopwords": True,
            "applyToEmojis": True
        },
        "countPenalty": {
            "scale": 0,
            "applyToWhitespaces": True,
            "applyToPunctuations": True,
            "applyToNumbers": True,
            "applyToStopwords": True,
            "applyToEmojis": True
        }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer "+settings.AI_API_KEY
    }


    

    def generate_response(self,prompt):
        ans = self.get_answer(prompt)
        entit = self.get_entities(prompt)

        team, matches = ans

        if team == "":
            return "There is no matches in the indicated date."
        else:
            adj = entit["ADJ"][0]
            desc = "won" if adj == "best" else "lost"
            if len(entit["ENT"]) == 0:
                pro = f"Write a sentence saying that the {adj} team in the Bundesliga is {team} with {matches} {desc} matches"
                
            
            elif len(entit["ENT"]) == 1:
                ent = entit["ENT"][0]
                pro = f"Write a sentence saying that the {adj} team in the Bundesliga in {ent} is {team} with {matches} {desc} matches"
                
            else:
                ent0, ent1 = entit["ENT"]
                pro = f"Write a sentence saying that the {adj} team in the Bundesliga between {ent0} and {ent1} is {team} with {matches} {desc} matches"
                      
            self.payload["prompt"] = pro
            response = requests.post(self.url, json=self.payload, headers=self.headers)
            obj = json.loads(response.text)
            return obj["completions"][0]["data"]["text"]
            




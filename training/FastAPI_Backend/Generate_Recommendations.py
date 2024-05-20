import requests
import json

class Generator:
    def __init__(self,nutrition_input:list,include_ingredients:list=[],exclude_ingredients:list=[],params:dict={'n_neighbors':5,'return_distance':False}):
        self.nutrition_input=nutrition_input
        self.include_ingredients=include_ingredients
        self.exclude_ingredients=exclude_ingredients
        self.params=params

    def set_request(self,nutrition_input:list,include_ingredients:list,exclude_ingredients:list,params:dict):
        self.nutrition_input=nutrition_input
        self.include_ingredients=include_ingredients
        self.exclude_ingredients=exclude_ingredients
        self.params=params

    def generate(self,):
        request={
            'nutritionInput':self.nutrition_input,
            'includeIngredients':self.include_ingredients,
            'excludeIngredients':self.exclude_ingredients,
            'params':self.params
        }
        response=requests.post(url='http://localhost:8085/predict/',data=json.dumps(request))
        return response

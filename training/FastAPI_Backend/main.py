from fastapi import FastAPI # type: ignore
from pydantic import BaseModel,conlist # type: ignore
from typing import List,Optional
import pandas as pd # type: ignore
from model import recommend,output_recommended_recipes
from random import uniform as rnd
from Generate_Recommendations import Generator
from ImageFinder.ImageFinder import get_images_links as find_image
from typing import Dict

dataset=pd.read_csv('../Data/dataset_unzip.csv')

app = FastAPI()



class PersonIn(BaseModel):
    age: int
    height: float
    weight: float
    gender: str
    activity: str
    meals_calories_perc: Dict[str, float]
    weight_loss: float

class params(BaseModel):
    n_neighbors:int=5
    return_distance:bool=False

class PredictionIn(BaseModel):
    nutrition_input:conlist(float, min_items=9, max_items=9) # type: ignore
    ingredients:list[str]=[]
    params:Optional[params]


class Recipe(BaseModel):
    name:str
    cookTime:str
    prepTime:str
    totalTime:str
    recipeIngredientsParts:list[str]
    calories:float
    fatContent:float
    saturatedFatContent:float
    cholesterolContent:float
    sodiumContent:float
    carbohydrateContent:float
    fiberContent:float
    sugarContent:float
    proteinContent:float
    recipeInstructions:list[str]
    images:list[str]

class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None

class Person:
    def __init__(self,age,height,weight,gender,activity,meals_calories_perc,weight_loss):
        self.age=age
        self.height=height
        self.weight=weight
        self.gender=gender
        self.activity=activity
        self.meals_calories_perc=meals_calories_perc
        self.weight_loss=weight_loss
    def calculate_bmi(self,):
        bmi=round(self.weight/((self.height/100)**2),2)
        return bmi

    def display_result(self,):
        bmi=self.calculate_bmi()
        bmi_string=f'{bmi} kg/m²'
        if bmi<18.5:
            category='Underweight'
            color='Red'
        elif 18.5<=bmi<25:
            category='Normal'
            color='Green'
        elif 25<=bmi<30:
            category='Overweight'
            color='Yellow'
        else:
            category='Obesity'    
            color='Red'
        return bmi_string,category,color

    def calculate_bmr(self):
        if self.gender=='Male':
            bmr=10*self.weight+6.25*self.height-5*self.age+5
        else:
            bmr=10*self.weight+6.25*self.height-5*self.age-161
        return bmr

    def calories_calculator(self):
        activites=['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)', 'Very active (6-7 days/wk)', 'Extra active (very active & physical job)']
        weights=[1.2,1.375,1.55,1.725,1.9]
        weight = weights[activites.index(self.activity)]
        maintain_calories = self.calculate_bmr()*weight
        return maintain_calories

    def generate_recommendations(self,):
        total_calories=self.weight_loss*self.calories_calculator()
        output=[]
        for meal in self.meals_calories_perc:
            meal_calories=self.meals_calories_perc[meal]*total_calories
            if meal=='breakfast':        
                recommended_nutrition = [meal_calories,rnd(10,30),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,10),rnd(0,10),rnd(30,100)]
            elif meal=='lunch':
                recommended_nutrition = [meal_calories,rnd(20,40),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,20),rnd(0,10),rnd(50,175)]
            elif meal=='dinner':
                recommended_nutrition = [meal_calories,rnd(20,40),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,20),rnd(0,10),rnd(50,175)] 
            else:
                recommended_nutrition = [meal_calories,rnd(10,30),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,10),rnd(0,10),rnd(30,100)]
            recommendation_dataframe=recommend(dataset,recommended_nutrition,[],{'n_neighbors':5,'return_distance':False})
            output.append(output_recommended_recipes(recommendation_dataframe))
        for recommendation in output:
            for recipe in recommendation:
                recipe['images']=find_image(recipe['Name']) 
        if output is None:
            return {"data":None}
        else:
            return {"data":output}
@app.get("/")
def home():
    return {"health_check": "OK"}


@app.post("/predict/",response_model=PredictionOut)
def update_item(prediction_input:PredictionIn):
    recommendation_dataframe=recommend(dataset,prediction_input.nutrition_input,prediction_input.ingredients,prediction_input.params.dict())
    output=output_recommended_recipes(recommendation_dataframe)
    if output is None:
        return {"data":None}
    else:
        return {"data":output}
    
@app.post("/recommend/")
def recommendation(person: PersonIn):

    person_obj = Person(
        age=person.age,
        height=person.height,
        weight=person.weight,
        gender=person.gender,
        activity=person.activity,
        meals_calories_perc=person.meals_calories_perc,
        weight_loss=person.weight_loss
    )
    
    recommendations = person_obj.generate_recommendations()

    if recommendations is None:
        return None
    else:
        return recommendations

    


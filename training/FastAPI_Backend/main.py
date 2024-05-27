from fastapi import FastAPI # type: ignore
from pydantic import BaseModel,conlist,Field # type: ignore
from typing import List,Optional
import pandas as pd # type: ignore
from model import recommend,output_recommended_recipes, extract_data
from random import uniform as rnd
from Generate_Recommendations import Generator
from ImageFinder.ImageFinder import get_images_links as find_image
from typing import Dict
import pymysql.cursors
import pandas as pd
import datetime
from sqlalchemy import Column, Integer, String, Date, Boolean, Enum, ForeignKey, create_engine
from sqlalchemy.orm import relationship,sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from save_plan import save_recommendations


from db_config import db_config

cnx = pymysql.connect(**db_config)

try:
    with cnx.cursor() as cursor:
        sql = "SELECT * FROM food_recipe"
        cursor.execute(sql)
        rows = cursor.fetchall()
finally:
    cnx.close()

columns_to_keep = ['recipe_id', 'name', 'cook_time', 'prep_time','images', 'total_time', 'recipe_ingredients_parts', 'calories', 'fat_content', 'saturated_fat_content', 'cholesterol_content', 'sodium_content', 'carbonhydrate_content', 'fiber_content', 'sugar_content', 'protein_content', 'recipe_instructions']
dataset = pd.DataFrame(rows, columns=columns_to_keep)
# dataset=pd.read_csv('../Data/updated_dataset.csv')


app = FastAPI()


class PersonIn(BaseModel):
    id: int
    age: int
    height: float
    weight: float
    gender: str
    activity: str
    mealsCaloriesPerc: Dict[str, float]
    weightLoss: float
    includeIngredients: List[str] = Field(default_factory=list)
    excludeIngredients: List[str] = Field(default_factory=list)

class params(BaseModel):
    n_neighbors:int=5
    return_distance:bool=False

class PredictionIn(BaseModel):
    nutrition_input:conlist(float, min_items=9, max_items=9) # type: ignore
    includeIngredients:list[str]=[]
    excludeIngredients:list[str]=[]
    params:Optional[params]


class Recipe(BaseModel):
    name:str
    totalTime:str
    calories:float
    images:list[str]
    

class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None

class Person:
    def __init__(self,id,age,height,weight,gender,activity,mealsCaloriesPerc,weightLoss,includeIngredients, excludeIngredients):
        self.user_id=id
        self.age=age
        self.height=height
        self.weight=weight
        self.gender=gender
        self.activity=activity
        self.mealsCaloriesPerc=mealsCaloriesPerc
        self.weightLoss=weightLoss
        self.includeIngredients=includeIngredients
        self.excludeIngredients=excludeIngredients
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

    

    def generate_recommendations(self, day_count):
        weight_loss_factors = {1: 0.7, 2: 1.3, 3: 1}
        total_calories = weight_loss_factors[self.weightLoss] * self.calories_calculator()
        output=[]
        extracted_data = extract_data(dataset, self.includeIngredients, self.excludeIngredients)
        for i in range(day_count):
            daily_output = {'date': String,'breakfast': [], 'lunch': [], 'dinner': [], 'morningSnack': [], 'afternoonSnack': []}
            date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%d-%m-%Y')
            daily_output["date"] = date
            for meal in self.mealsCaloriesPerc:
                meal_calories=self.mealsCaloriesPerc[meal]*total_calories
                if meal=='breakfast':        
                    recommended_nutrition = [meal_calories,rnd(10,30),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,10),rnd(0,10),rnd(30,100)]
                elif meal=='lunch':
                    recommended_nutrition = [meal_calories,rnd(20,40),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,20),rnd(0,10),rnd(50,175)]
                elif meal=='dinner':
                    recommended_nutrition = [meal_calories,rnd(20,40),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,20),rnd(0,10),rnd(50,175)] 
                else:
                    recommended_nutrition = [meal_calories,rnd(10,30),rnd(0,4),rnd(0,30),rnd(0,400),rnd(40,75),rnd(4,10),rnd(0,10),rnd(30,100)]
                recommendation_dataframe=recommend(extracted_data,recommended_nutrition,[],[],{'n_neighbors':5,'return_distance':False})
                daily_output[meal] = output_recommended_recipes(recommendation_dataframe)
            
            output.append(daily_output)
        # save_recommendations(self.user_id, output, total_calories)
        if not output:
            return {"statusCode": 401, "message": "No recommendations generated", "data": None}
        else:
            return {"statusCode": 200, "message": "Recommendations generated successfully", "data": {"recommendCalories": round(total_calories),"bmi":self.calculate_bmi(), "recommendations": output}}
@app.get("/")
def home():
    return {"health_check": "OK"}


# @app.post("/predict",response_model=PredictionOut)
# def update_item(prediction_input:PredictionIn):
#     recommendation_dataframe=recommend(dataset,prediction_input.nutrition_input,prediction_input.includeIngredients, prediction_input.excludeIngredients,prediction_input.params.dict())
#     output=output_recommended_recipes(recommendation_dataframe)
#     if output is None:
#         return {"data":None}
#     else:
#         return {"data":output}
    
@app.post("/recommend")
def recommendation(person: PersonIn,dayCount:int=1):

    person_obj = Person(
        id=person.id,
        age=person.age,
        height=person.height,
        weight=person.weight,
        gender=person.gender,
        activity=person.activity,
        mealsCaloriesPerc=person.mealsCaloriesPerc,
        weightLoss=person.weightLoss,
        includeIngredients=person.includeIngredients,
        excludeIngredients=person.excludeIngredients
    )
    
    recommendations = person_obj.generate_recommendations(dayCount)

    if recommendations is None:
        return None
    else:
        return recommendations

    


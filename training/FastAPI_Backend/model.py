import numpy as np
import pandas as pd
import re
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
import time
import logging


def scaling(dataframe):
    columns_to_scale = ['calories', 'fat_content', 'saturated_fat_content', 'cholesterol_content', 'sodium_content', 'carbonhydrate_content', 'fiber_content', 'sugar_content', 'protein_content']
    scaler=StandardScaler()
    prep_data=scaler.fit_transform(dataframe[columns_to_scale].to_numpy())
    return prep_data,scaler

def nn_predictor(prep_data):
    neigh = NearestNeighbors(metric='cosine',algorithm='brute')
    neigh.fit(prep_data)
    return neigh

def build_pipeline(neigh,scaler,params):
    transformer = FunctionTransformer(neigh.kneighbors,kw_args=params)
    pipeline=Pipeline([('std_scaler',scaler),('NN',transformer)])
    return pipeline

def extract_data(dataframe,include_ingredients, exclude_ingredients):
    extracted_data=dataframe.copy()
    extracted_data=extract_ingredient_filtered_data(extracted_data,include_ingredients, exclude_ingredients)
    return extracted_data
    
# def extract_ingredient_filtered_data(dataframe,ingredients):
#     extracted_data=dataframe.copy()
#     regex_string=''.join(map(lambda x:f'(?=.*{x})',ingredients))
#     extracted_data = extracted_data[~extracted_data['RecipeIngredientParts'].str.contains(regex_string, regex=True, flags=re.IGNORECASE)]
#     return extracted_data

def extract_ingredient_filtered_data(dataframe, include_ingredients, exclude_ingredients):
    start_time = time.time()
    extracted_data = dataframe.copy()
    
    if include_ingredients:
        include_regex_string = ''.join(map(lambda x: f'(?=.*{x})', include_ingredients))
        extracted_data = extracted_data[extracted_data['recipe_ingredients_parts'].str.contains(include_regex_string, regex=True, flags=re.IGNORECASE)]
    
    if exclude_ingredients:
        exclude_regex_string = ''.join(map(lambda x: f'(?=.*{x})', exclude_ingredients))
        extracted_data = extracted_data[~extracted_data['recipe_ingredients_parts'].str.contains(exclude_regex_string, regex=True, flags=re.IGNORECASE)]
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time of extract_ingredient_filtered_data function: {elapsed_time} seconds")
    return extracted_data

def apply_pipeline(pipeline,_input,extracted_data):
    _input=np.array(_input).reshape(1,-1)
    return extracted_data.iloc[pipeline.transform(_input)[0]]

def recommend(dataframe,_input,include_ingredients=[], exclude_ingredients=[],params={'n_neighbors':5,'return_distance':False}):
        
        extracted_data=extract_data(dataframe,include_ingredients, exclude_ingredients)
        start_time = time.time()
        if extracted_data.shape[0]>=params['n_neighbors']:
            
            prep_data,scaler=scaling(extracted_data)
            neigh=nn_predictor(prep_data)
            pipeline=build_pipeline(neigh,scaler,params)
        
            return apply_pipeline(pipeline,_input,extracted_data)
        else:
            return None

def extract_quoted_strings(s):
    # Find all the strings inside double quotes
    strings = re.findall(r'"((?:[^"\\]|\\.)*)"', s)
    # Join the strings with 'and'
    return strings

def output_recommended_recipes(dataframe):
    if dataframe is not None:
        columns_to_drop = ['cook_time', 'prep_time', 'recipe_ingredients_parts', 'fat_content', 'saturated_fat_content', 'cholesterol_content', 'sodium_content', 'carbonhydrate_content', 'fiber_content', 'sugar_content', 'protein_content','recipe_instructions']
        output = dataframe.drop(columns=columns_to_drop).copy()
        output.columns = [col[0].lower() + col.title().replace('_', '')[1:] for col in output.columns]
        output['images'] = output['images'].apply(split_string_to_list)
        output['totalTime'] = output['totalTime'].apply(process_time)
        output = output.to_dict("records")
        # for recipe in output:
        #     recipe['RecipeIngredientParts']=extract_quoted_strings(recipe['RecipeIngredientParts'])
        #     recipe['RecipeInstructions']=extract_quoted_strings(recipe['RecipeInstructions'])
            # recipe['Images']=extract_quoted_strings(recipe['Images'])
    else:
        output=None
    return output

def split_string_to_list(input):
    if input is None:
        return []
    if not input.startswith("c"):
        return [input.strip('"')]
    input = input[3:-1]
    items = input.split(", ")
    for i in range(len(items)):
        items[i] = items[i].strip('"').replace("\\", "").replace("\n", "").replace('\\"', '')
    return items

def process_time(time):
    if time is None:
        return ""
    if time.startswith("PT"):
        return time.replace("PT", "", 1)
    return time
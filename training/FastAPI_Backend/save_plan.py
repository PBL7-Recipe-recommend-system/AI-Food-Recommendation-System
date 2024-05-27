from sqlalchemy.orm import Session 
from sqlalchemy import Column, Integer, String, Date, Boolean, Enum, ForeignKey, create_engine,Float, Text, DateTime
from sqlalchemy.orm import relationship,sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from db_config import db_config

DATABASE_URL = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"

Base = declarative_base()



Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150))
    email = Column(String, nullable=False, unique=True)
    height = Column(Float)
    weight = Column(Float)
    dietary_goal = Column(Integer)
    password = Column(Text, nullable=False)
    created_at = Column(Date)
    gender = Column(String)
    avatar = Column(String)
    daily_activities = Column(String)
    meals = Column(Integer)
    birthday = Column(Date)
    active = Column(Boolean)
    is_custom_plan = Column(Boolean)
    otp = Column(String)
    otp_generated_time = Column(DateTime)

    include_ingredients = relationship('UserIncludeIngredient', back_populates='user')
    exclude_ingredients = relationship('UserExcludeIngredient', back_populates='user')



class UserIncludeIngredient(Base):
    
    __tablename__ = 'user_include_ingredient'
    include_ingredient_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    user = relationship('User', back_populates='include_ingredients')

class UserExcludeIngredient(Base):

    __tablename__ = 'user_exclude_ingredient'
    exclude_ingredient_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    user = relationship('User', back_populates='exclude_ingredients')

class RecommendMealPlan(Base):
    __tablename__ = 'recommend_meal_plan'

    recommend_meal_plan_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    daily_calorie = Column(Integer)
    description = Column(String(255))

    recipes = relationship('RecommendMealPlanRecipes', back_populates='meal_plan')

class RecommendMealPlanRecipes(Base):
    __tablename__ = 'recommend_meal_plan_recipes'
    recommend_meal_plan_id = Column(Integer, ForeignKey('recommend_meal_plan.recommend_meal_plan_id'), primary_key=True)
    recipe_id = Column(Integer, ForeignKey('food_recipe.recipe_id'), primary_key=True)
    meal_type = Column(Enum('breakfast', 'lunch', 'dinner', 'morningSnack', 'afternoonSnack'),  primary_key=True)
    is_cook = Column(Boolean, default=False)

    meal_plan = relationship('RecommendMealPlan', back_populates='recipes')

class FoodRecipe(Base):
    __tablename__ = 'food_recipe'

    recipe_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    author_name = Column(String, nullable=False)
    cook_time = Column(String)
    prep_time = Column(String)
    total_time = Column(String)
    date_published = Column(Date, nullable=False)
    description = Column(String)
    images = Column(String)
    recipe_category = Column(String)
    keywords = Column(String)
    recipe_ingredients_quantities = Column(String)
    recipe_ingredients_parts = Column(String)
    aggregated_ratings = Column(Integer)
    review_count = Column(Integer)
    calories = Column(Float)
    fat_content = Column(Float)
    saturated_fat_content = Column(Float)
    cholesterol_content = Column(Float)
    sodium_content = Column(Float)
    carbonhydrate_content = Column(Float)
    fiber_content = Column(Float)
    sugar_content = Column(Float)
    protein_content = Column(Float)
    recipe_servings = Column(Integer)
    recipe_instructions = Column(String)



def save_recommendations(user_id, output, daily_calories):
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine, autoflush=False)

    try:
        for daily_output in output:
            date = datetime.strptime(daily_output['date'], '%d-%m-%Y').strftime('%Y-%m-%d')

            session = Session()
            meal_plan = session.query(RecommendMealPlan).filter_by(user_id=user_id, date=date).first()

            if meal_plan is None:
                meal_plan = RecommendMealPlan(
                    user_id=user_id,
                    date=date,
                    daily_calorie=daily_calories,
                    description="Generated meal plan"
                )
                session.add(meal_plan)
                session.commit()  

            for meal, recipes in daily_output.items():
                if meal != 'date':
                    for recipe in recipes:
                        meal_plan_recipe = session.query(RecommendMealPlanRecipes).filter_by(recommend_meal_plan_id=meal_plan.recommend_meal_plan_id, meal_type=meal).first()

                        if meal_plan_recipe is None:
                            meal_plan_recipe = RecommendMealPlanRecipes(
                                recommend_meal_plan_id=meal_plan.recommend_meal_plan_id,
                                recipe_id=recipe['recipeId'], 
                                meal_type=meal,
                                is_cook=False
                            )
                            session.add(meal_plan_recipe)
                        else:
                            meal_plan_recipe.recipe_id = recipe['recipeId']
                            meal_plan_recipe.is_cook = False
                        session.commit()
            session.close()

    except SQLAlchemyError as e:
        print(f"Failed to save recommendations: {e}")
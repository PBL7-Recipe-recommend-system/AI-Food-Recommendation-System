from sqlalchemy.orm import Session 
from sqlalchemy import Column, Integer, String, Date, Boolean, Enum, ForeignKey, create_engine
from sqlalchemy.orm import relationship,sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from db_config import db_config

DATABASE_URL = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"

Base = declarative_base()

class RecommendMealPlan(Base):
    __tablename__ = 'recommend_meal_plan'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    daily_calorie = Column(Integer)
    description = Column(String(255))

    recipes = relationship('RecommendMealPlanRecipes', backref='meal_plan')

class RecommendMealPlanRecipes(Base):
    __tablename__ = 'recommend_meal_plan_recipes'

    meal_plan_id = Column(Integer, ForeignKey('recommend_meal_plan.id'), primary_key=True)
    recipe_id = Column(Integer, primary_key=True)
    meal_type = Column(Enum('breakfast', 'lunch', 'dinner', 'morningSnack', 'afternoonSnack'), primary_key=True)
    is_cook = Column(Boolean, default=False)

def save_recommendations(user_id, output, total_calories):
    engine = create_engine(DATABASE_URL)

# Create a sessionmaker bound to this engine
    Session = sessionmaker(bind=engine)
    # Start a new session
    session = Session()

    for recommendation in output:
        meal_plan = RecommendMealPlan(
            user_id=user_id,
            date=recommendation['date'],
            daily_calorie=total_calories,
            description='Recommended meal plan'
        )

        for meals, recipes in recommendation['meals'].items():
            for recipe in recipes:
                meal_plan_recipe = RecommendMealPlanRecipes(
                    meal_plan_id=meal_plan.id,
                    recipe_id=recipe['recipeId'],
                    meal_type=meals,
                    is_cook=False
                )
                session.add(meal_plan_recipe)

        session.add(meal_plan)

    # Commit the transaction
    session.commit()
    session.close()
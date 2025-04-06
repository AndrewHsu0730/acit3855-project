from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, func


class Base(DeclarativeBase):
    pass


class Workout(Base):
    __tablename__ = "workout"
    workout_id = mapped_column(String(20), primary_key = True)
    # workout_id = mapped_column(Integer, primary_key = True, autoincrement = True)
    weight_lifted = mapped_column(Integer, nullable = False)
    duration = mapped_column(Integer, nullable = False)
    timestamp = mapped_column(DateTime, nullable = False)
    date_created = mapped_column(DateTime, nullable = False, default = func.now())
    trace_id = mapped_column(String(50), nullable = False, unique = True)

    def to_dict(self):
        data = {
            "workout_id": self.workout_id,
            "weight_lifted": self.weight_lifted,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "date_created": self.date_created,
            "trace_id": self.trace_id
        }
        # print(data)
        return data


class Diet(Base):
    __tablename__ = "diet"
    diet_id = mapped_column(String(20), primary_key = True)
    # diet_id = mapped_column(Integer, primary_key = True, autoincrement = True)
    carb = mapped_column(String(30), nullable = False)
    protein = mapped_column(String(30), nullable = False)
    veg = mapped_column(String(30), nullable = False)
    calorie_intake = mapped_column(Integer, nullable = False)
    timestamp = mapped_column(DateTime, nullable = False)
    date_created = mapped_column(DateTime, nullable = False, default = func.now())
    trace_id = mapped_column(String(50), nullable = False, unique = True)

    def to_dict(self):
        data = {
            "diet_id": self.diet_id,
            "carb": self.carb,
            "protein": self.protein,
            "veg": self.veg,
            "calorie_intake": self.calorie_intake,
            "timestamp": self.timestamp,
            "date_created": self.date_created,
            "trace_id": self.trace_id
        }
        # print(data)
        return data

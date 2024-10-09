from .managers import PetitionManager
from .managers import StatisticsManager

from app.db import DataBase

from app.config import settings

db = DataBase(settings.host, settings.port, settings.user, settings.database, settings.password)
petition_manager = PetitionManager(db)
statistics_manager = StatisticsManager(db)
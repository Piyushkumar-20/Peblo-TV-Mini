from pydantic import BaseModel, ConfigDict, Field


class SeasonBase(BaseModel):
    season_number: int = Field(ge=0)


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    season_number: int | None = Field(default=None, ge=0)


class SeasonRead(SeasonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    show_id: int
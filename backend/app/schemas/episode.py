from pydantic import BaseModel, ConfigDict, Field


class EpisodeBase(BaseModel):
    episode_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    synopsis: str | None = None
    duration_seconds: int | None = Field(default=None, gt=0)
    language: str = Field(min_length=1, max_length=50)
    content_group: str = Field(min_length=1, max_length=255)
    is_published: bool = False


class EpisodeCreate(EpisodeBase):
    pass


class EpisodeUpdate(BaseModel):
    episode_number: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    synopsis: str | None = None
    duration_seconds: int | None = Field(default=None, gt=0)
    language: str | None = Field(default=None, min_length=1, max_length=50)
    content_group: str | None = Field(default=None, min_length=1, max_length=255)
    is_published: bool | None = None


class EpisodeRead(EpisodeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season_id: int
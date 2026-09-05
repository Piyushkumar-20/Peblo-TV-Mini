from pydantic import BaseModel, ConfigDict, Field


class ShowBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    synopsis: str | None = None
    categories: list[str] = Field(default_factory=list)
    section: str | None = Field(default=None, max_length=100)
    language: str = Field(min_length=1, max_length=50)
    is_published: bool = False


class ShowCreate(ShowBase):
    pass


class ShowUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    synopsis: str | None = None
    categories: list[str] | None = None
    section: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, min_length=1, max_length=50)
    is_published: bool | None = None


class ShowRead(ShowBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
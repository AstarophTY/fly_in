from pydantic import BaseModel, Field, ValidationError, model_validator



class ParsingValidator(BaseModel):
    nb_drones: int = Field(ge=1)
    
    @model_validator(mode='after')
    def validator():
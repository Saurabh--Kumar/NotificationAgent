from typing import List
from pydantic import BaseModel, Field
from uuid import UUID


class Company(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the company")
    name: str = Field(..., description="Company name")

    model_config = {"from_attributes": True}


class CompanyList(BaseModel):
    companies: List[Company] = []

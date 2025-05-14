from fastapi import FastAPI
import question_creation as qc
import question_categorization as qcat
from pydantic import BaseModel

app = FastAPI()

class QCModel(BaseModel):
    message:str

class Question(BaseModel):
    question:str
    options:list[str]
    answer:list[str]


class QCatModel(BaseModel):
    groupId:int
    groupText:str
    questions:list[Question]

class RequestCatModel(BaseModel):
    requestCat:list[str]
    questionGroups:list[QCatModel]


@app.post('/question_creation')
async def question_creation(request_model :  QCModel):
    return qc.question_creation(request_model.message)

@app.post('/question_categorization')
async def question_categorization(request_model : RequestCatModel):
    # print(request_model)
    return qcat.question_categorization(request_model.model_dump_json())



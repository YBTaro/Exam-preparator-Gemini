from google import genai

from google.genai import types
from dataclasses import dataclass

from IPython.display import HTML, Markdown, display
from google.api_core import retry
import typing_extensions as typing
import json


with open('config.json') as f:
    config = json.load(f)

api_key = config['api_key']

def question_categorization(message:str):
    is_retriable = lambda e: (isinstance(e, genai.errors.APIError) and e.code in {429, 503})

    genai.models.Models.generate_content = retry.Retry(
    predicate=is_retriable)(genai.models.Models.generate_content)

    client = genai.Client(api_key=api_key)

    @dataclass
    class QuestionGroupCat(typing.TypedDict):
        groupId:int
        categories:list[str]

    instruction = """
    You are given the following input data structures:
        class Question(BaseModel):
            question: str
            options: list[str]
            answer: list[str]

        class QCatModel(BaseModel):
            groupId: int
            groupText: str
            questions: list[Question]

        class RequestCatModel(BaseModel):
            requestCat: list[str]   # predefined list of available categories
            questionGroups: list[QCatModel]

    You must produce the following output structure:
        @dataclass
        class QuestionGroupCat(typing.TypedDict):
            groupId: int
            categories: list[str]
    Task:

        - For each question group in the questionGroups list, determine which categories it belongs to.

        - You are only allowed to assign categories from the provided requestCat list.

        - If a group contains multiple questions, you must consider:

            1. The groupText

            2. All the questions, options and their answers together to determine the best fitting categories.

        - If a group contains only one question, you should categorize based solely on that single question, options and its answer.

        - It is possible for a group to have:

            1. Multiple categories

            2. Zero categories (if no appropriate category matches)

        - Be precise: analyze carefully whether the questions relate to the provided categories.

        - Return the results as a list of QuestionGroupCat objects, matching each groupId with the assigned list of categories.

    Input:
        The JSON of the RequestCatModel will be sent as the payload.

    Output:
        A list of QuestionGroupCat, correctly categorizing each group according to the above rules.

        

    Example 1:
        input:
            {
                "requestCat": ["Geography", "Biology"],
                "questionGroups": [
                    {
                    "groupId": 1,
                    "groupText": "Answer the question below",
                    "questions": [
                        {
                        "question": "Which is the largest continent?",
                        "options": ["Africa", "Asia", "Europe", "Australia"],
                        "answer": ["Asia"]
                        },
                        {
                        "question": "Which continent is known as the 'Dark Continent'?",
                        "options": ["Africa", "South America", "Europe", "Asia"],
                        "answer": ["Africa"]
                        }
                    ]
                    },
                    {
                    "groupId": 2,
                    "groupText": "",
                    "questions": [
                        {
                        "question": "What organ pumps blood through the body?",
                        "options": ["Lungs", "Liver", "Heart", "Kidneys"],
                        "answer": ["Heart"]
                        }
                    ]
                    },
                    {
                    "groupId": 3,
                    "groupText": "",
                    "questions": [
                        {
                        "question": "Who wrote 'Pride and Prejudice'?",
                        "options": ["Emily Bronte", "Charles Dickens", "Jane Austen", "William Shakespeare"],
                        "answer": ["Jane Austen"]
                        }
                    ]
                    }
                ]
            }
        output:
        [
            {
                "groupId": 1,
                "categories": [
                    "Geography"
                ]
            },
            {
                "groupId": 2,
                "categories": [
                    "Biology"
                ]
            },
            {
                "groupId": 3,
                "categories": []
            }
        ]

    """
    document = """


    """
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=list[QuestionGroupCat],
            system_instruction=instruction
        ),
        contents=message)
    json_data = json.loads(response.text)

    # print(json_data)
    return json_data
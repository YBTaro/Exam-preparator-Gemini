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
def question_creation(message:str):
  is_retriable = lambda e: (isinstance(e, genai.errors.APIError) and e.code in {429, 503})

  genai.models.Models.generate_content = retry.Retry(
      predicate=is_retriable)(genai.models.Models.generate_content)

  client = genai.Client(api_key=api_key)






  @dataclass
  class Question(typing.TypedDict):
      question:str
      options:list[str]
      q_type:str
      ans:list[str]
      ai_ans:bool
      order:int
  @dataclass
  class QuestionGroup(typing.TypedDict):
      groupText:str
      questions:list[Question]





  instruction = """
  Role: You are a professional question parser and formatter.

  Task Overview:
  You will be given a document that contains either standalone questions or groups of related questions. Ignore the test instructions section (if any). Your goal is to extract and convert the content into a structured Python-style dictionary format.
  Some questions may contain a mixture of different languages (e.g., Chinese, English, etc.). You must correctly parse and process all questions, regardless of the language used.
  nsure that all content is considered and correctly handled without omission or misalignment due to language differences.

  class Question(typing.TypedDict):
      question: str           # The core question text (excluding any options)
      options: list[str]      # List of answer choices, if applicable; otherwise []
      q_type: str             # The question type (see allowed values below)
      ans: list[str]          # List of correct answers; generate one if missing
      ai_ans: bool            # if answer is AI-generated; False if provided
      order: int              # Position in the group; always 1 if standalone

  class QuestionSet(typing.TypedDict):
      groupText: str          # Shared prompt for grouped questions; "" for standalone
      questions: list[Question]

    Description | q_type Value: 
      Multiple choice | "multi"
      Single choice | "single"
      True/False (Yes/No) | "true_false"
      Short answer (brief text) | "brief"
      Fill in the blank | "fill"
      Ordering / Sorting | "ordering"
      Matching / Pairing | "matching"

      
  1. Identify Questions and Groups::
    - Parse the document to extract individual questions or grouped sets.
    - If multiple questions refer to a shared context or prompt, group them under one QuestionSet using groupText.
    - For standalone questions, set groupText to an empty string "".
  
  2. Determine Question Type (q_type)
    - Assign the appropriate q_type based on the question’s format or intent.

  3. Extract Answer Choices (if applicable):
    - If the question is multiple choice, single choice, ordering question, extract them as a list.
    - For other types including pairing question, leave the options field as an empty list [].
  
  4. Identify or Generate the Answer
    - If an answer is explicitly provided, use it and set ai_ans = False.
    - If no answer is provided, generate a reasonable answer and set ai_ans = True.
    - For ordering questions, list the options in the correct sequence as the answer.
    - For pairing questions, each answer entry should represent one correct pair, and all pairs should be listed.
    - For multiple choice questions, include all correct options in the answer.
    - Even for other tpye of questions, the answer must be enclosed in a list containing a single string.

  5. Assign Order (order)
    - In grouped questions, set the order field based on their order in the group (starting from 1).
    - Standalone questions always have order = 1.


  Example 1:
    Document:
      1. What is the capital of France?
      2. Which of the following are programming languages? 
        (A) Python 
        (B) HTML 
        (C) Banana 
        (D) JavaScript
      3. Explain why the water cycle is important to the environment.
      4. True or False: The Earth is flat. (False)
      5. Match the following:
        1. Sun  A. Star
        2. Moon - B. Planet
        3. Earth - C. Satellite


      
    Expected Output Format:
    [
  {
    "groupText": "",
    "questions": [
      {
        "question": "What is the capital of France?",
        "options": [],
        "q_type": "brief",
        "ans": ["Paris"],
        "ai_ans": true,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "Which of the following are programming languages?",
        "options": ["Python", "HTML", "Banana", "JavaScript"],
        "q_type": "multi",
        "ans": ["Python", "HTML", "JavaScript"],
        "ai_ans": true,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "Explain why the water cycle is important to the environment.",
        "options": [],
        "q_type": "brief",
        "ans": ["It helps in distributing and recycling water, which supports ecosystems and life on Earth."],
        "ai_ans": true,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "True or False: The Earth is flat.",
        "options": [],
        "q_type": "true_false",
        "ans": ["False"],
        "ai_ans": false,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "Match the following: 1. Sun - A. Star, 2. Moon - B. Planet, 3. Earth - C. Satellite",
        "options": [],
        "q_type": "matching",
        "ans": ["Sun - Star", "Moon - Satellite", "Earth - Planet"],
        "ai_ans": true,
        "order": 1
      }
    ]
  }
]



  Example 2:
    Document:
      測驗說明：
      這是國中教育會考國文科試題本，試題本採雙面印刷，共 14頁，有 42 題
      選擇題，每題都只有一個正確或最佳的答案。測驗時間從 13：50 到 
      15：00，共 70 分鐘。作答開始與結束請聽從監試委員的指示。
      注意事項：
      1. 所有試題均為四選一的選擇題，答錯不倒扣，分為單題與題組兩個部
      分。
      2. 題組是指共用問題情境的數道試題，包括「選文」及兩題以上的相關
      試題。作答時請務必仔細閱讀選文的內容，再依問題做成判斷。
      3. 部分試題中的詞語，將於該題右下角加註，以利參考。
      4. 依試場規則規定，答案卡上不得書寫姓名座號，也不得作任何標記。
      故意汙損答案卡、損壞試題本，或在答案卡上顯示自己身分者，該科
      考試不予計列等級。
      作答方式：
      請依照題意從四個選項中選出一個正確或最佳的答案，並用 2B 鉛筆
      在答案卡上相應的位置畫記，請務必將選項塗黑、塗滿。如果需要修
      改答案，請使用橡皮擦擦拭乾淨，重新塗黑答案。例如答案為 B，則
      將    選項塗黑、塗滿，即：   
      以下為錯誤的畫記方式，可能導致電腦無法正確判讀。如：
          —未將選項塗滿
          —未將選項塗黑
          —未擦拭乾淨
          —塗出選項外
          —同時塗兩個選項
      國文科試題本
      113年國中教育會考
      請考生依指示
      填寫准考證末兩碼

      地球的自轉造成了白天與黑夜的交替，而公轉則是造成四季更替的重要因素。請說明地球自轉與公轉的差異。

      以下哪一項不是哺乳類動物？
      (A) 海豚(B) 蝙蝠(C) 章魚(D) 馬 Ans:C

      光合作用中，植物吸收的是哪一種氣體？
      A. 氧氣  
      B. 二氧化碳  
      C. 氮氣D. 氫氣

      水的冰點是0度C。
      yes

      人體中負責輸送氧氣的血球是__________。

      請閱讀以下資料，並回答29 ～ 30題：
      1990年代初研究人員設計出一套評估方法，是為了計算出當年度的「地球
      超載日」。今年（2022年）的「地球超載日」在7月28日，代表在這一天，我們
      已經耗盡當年度地球的永續資源，在剩餘的時間裡，都將以透支的方式消耗地
      球資源。據此，養活全世界的人口要1.75個地球的資源才夠。每個國家帶給地球
      的負擔也大不同，如果每個人的生活方式都跟美國人一樣，那2022年地球超載
      日會落在3月13日。
      根據這套方法往回推算1971年，地球超載日是12月25日，之後就一路提
      前。2000年地球超載日落在9月，2018年起提前到7月。2020年因Covid-19疫情爆
      發，地球超載日曾往後延了三週，但隔年就恢復到疫情前的情況。
      非政府組織世界自然基金會與全球生態足跡網將矛頭指向食品生產系統及
      其龐大的生態足跡：整體來說，地球上超過一半的生物承載力是用來養活人
      類。很大一部分的糧食和原物料是用於畜牧，人們再吃掉這些動物。富裕國家
      應減少肉品消費，如果可以將肉品消費量減半，地球超載日就可以延後17天。
      由於全世界1/3的食物被浪費掉，所以限制食物浪費可將超載日延後13天。
      ——改寫自「地球超載日」網站
      29. 

      根據本文，關於人類對地球資源的消耗，下列敘述何者最恰當？
      (A)1990年之前，人類並未透支地球資源
      (B)2022年人類耗用的地球資源是前一年的1.75倍
      (C)每年的地球超載日之後，全球資源就會消耗殆盡
      (D)美國人的生活方式比多數國家的人對地球造成更大的負擔
      30
      根據本文，下列何者最可能使地球超載日延後？
      (A)提升畜牧業整體產量
      (B)加強野生動物保育工作
      (C)增加飲食中蔬食的比例
      (D)嚴防Covid-19疫情再爆發

 Expected Output Format:
    [
  {
    "groupText": "",
    "questions": [
      {
        "question": "地球的自轉造成了白天與黑夜的交替，而公轉則是造成四季更替的重要因素。請說明地球自轉與公轉的差異。",
        "options": [],
        "q_type": "brief",
        "ans": ["地球自轉是指地球自身繞其軸心的旋轉，造成白天與黑夜的交替。公轉則是地球繞太陽的運動，造成四季更替。"],
        "ai_ans": true,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "以下哪一項不是哺乳類動物？",
        "options": ["海豚", "蝙蝠", "章魚", "馬"],
        "q_type": "single",
        "ans": ["章魚"],
        "ai_ans": false,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "光合作用中，植物吸收的是哪一種氣體？",
        "options": ["氧氣", "二氧化碳", "氮氣", "氫氣"],
        "q_type": "single",
        "ans": ["二氧化碳"],
        "ai_ans": true,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "水的冰點是0度C。",
        "options": [],
        "q_type": "trueFalse",
        "ans": ["yes"],
        "ai_ans": false,
        "order": 1
      }
    ]
  },
  {
    "groupText": "",
    "questions": [
      {
        "question": "人體中負責輸送氧氣的血球是__________。",
        "options": [],
        "q_type": "fill",
        "ans": ["紅血球"],
        "ai_ans": true,
        "order": 1
      }
    ]
  },
  {
    "groupText": "1990年代初研究人員設計出一套評估方法，是為了計算出當年度的「地球超載日」。今年（2022年）的「地球超載日」在7月28日，代表在這一天，我們已經耗盡當年度地球的永續資源，在剩餘的時間裡，都將以透支的方式消耗地球資源。據此，養活全世界的人口要1.75個地球的資源才夠。每個國家帶給地球的負擔也大不同，如果每個人的生活方式都跟美國人一樣，那2022年地球超載日會落在3月13日。根據這套方法往回推算1971年，地球超載日是12月25日，之後就一路提前。2000年地球超載日落在9月，2018年起提前到7月。2020年因Covid-19疫情爆發，地球超載日曾往後延了三週，但隔年就恢復到疫情前的情況。非政府組織世界自然基金會與全球生態足跡網將矛頭指向食品生產系統及其龐大的生態足跡：整體來說，地球上超過一半的生物承載力是用來養活人類。很大一部分的糧食和原物料是用於畜牧，人們再吃掉這些動物。富裕國家應減少肉品消費，如果可以將肉品消費量減半，地球超載日就可以延後17天。由於全世界1/3的食物被浪費掉，所以限制食物浪費可將超載日延後13天。

——改寫自「地球超載日」網站",
    "questions": [
      {
        "question": "根據本文，關於人類對地球資源的消耗，下列敘述何者最恰當？",
        "options": [
          "1990年之前，人類並未透支地球資源",
          "2022年人類耗用的地球資源是前一年的1.75倍",
          "每年的地球超載日之後，全球資源就會消耗殆盡",
          "美國人的生活方式比多數國家的人對地球造成更大的負擔"
        ],
        "q_type": "single",
        "ans": ["美國人的生活方式比多數國家的人對地球造成更大的負擔"],
        "ai_ans": true,
        "order": 1
      },
      {
        "question": 根據本文，下列何者最可能使地球超載日延後？",
        "options": [
          "提升畜牧業整體產量",
          "加強野生動物保育工作",
          "增加飲食中蔬食的比例",
          "嚴防Covid-19疫情再爆發"
        ],
        "q_type": "single",
        "ans": ["增加飲食中蔬食的比例"],
        "ai_ans": true,
        "order": 2
      }
    ]
  }
]


  Example 3:
  Document:
    請依正確洗手的步驟，將下列動作依序排列：

    (A) 沖
    (B) 濕
    (C) 搓
    (D) 擦
    (E) 捧

    A: 濕,搓,沖,捧,擦

    請將下列文學作品與其作者配對：

    (A)《哈姆雷特》
    (B)《紅樓夢》
    (C)《百年孤寂》
    (D)《老人與海》

    作者選項：
    (1) 莎士比亞
    (2) 馮夢龍
    (3) 馬奎斯
    (4) 海明威

   Expected Output Format:
   [
    {
      "groupText": "",
      "questions": [
        {
          "question": "請依正確洗手的步驟，將下列動作依序排列：",
          "options":  [
            "沖",
            "濕",
            "搓",
            "擦",
            "捧"
          ],
          "q_type": "ordering",
          "ans": [
            "濕",
            "搓",
            "沖",
            "捧",
            "擦"
          ],
          "ai_ans": false,
          "order": 1
        }
      ]
    },{
      "groupText": "",
      "questions": [
        {
          "question": "請將下列文學作品與其作者配對：
          (A)《哈姆雷特》
          (B)《紅樓夢》
          (C)《百年孤寂》
          (D)《老人與海》
          作者選項：
          (1) 莎士比亞
          (2) 馮夢龍
          (3) 馬奎斯
          (4) 海明威",
          "options": [],
          "q_type": "matching",
          "ans": [
          "《哈姆雷特》 - 莎士比亞",
          "《紅樓夢》 - 曹雪芹",
          "《百年孤寂》 - 馬奎斯",
          "《老人與海》 - 海明威"
          ],
          "ai_ans": true,
          "order": 1
        }
      ]
    }
  ]

  Example 4:
  Document: 
  請依四大名著的成書時間，將下列作品依序排列：

    (A) 西遊記
    (B) 紅樓夢
    (C) 水滸傳
    (D) 三國演義

    A: "三國演義","水滸傳","西遊記", "紅樓夢"

  請將下列音樂作品與其作曲家正確配對：

    (A)《小夜曲》
    (B)《命運交響曲》
    (C)《四季》
    (D)《天鵝湖》

    作曲家選項：
    (1) 柴可夫斯基
    (2) 莫札特
    (3) 維瓦第
    (4) 貝多芬

  Expected Output Format:
  [
    {
        "groupText": "",
        "questions": [
            {
                "question": "請依四大名著的成書時間，將下列作品依序排列：",
                "options": [
                    "西遊記",
                    "紅樓夢",
                    "水滸傳",
                    "三國演義"
                ],
                "q_type": "ordering",
                "ans": [
                    "三國演義",
                    "水滸傳",
                    "西遊記",
                    "紅樓夢"
                ],
                "ai_ans": false,
                "order": 1
            }
        ]
    },
    {
        "groupText": "",
        "questions": [
            {
                "question": "請將下列音樂作品與其作曲家正確配對：\n\n(A)《小夜曲》\n(B)《命運交響曲》\n(C)《四季》\n(D)《天鵝湖》\n\n作曲家選項：\n(1) 柴可夫斯基\n(2) 莫札特\n(3) 維瓦第\n(4) 貝多芬",
                "options": [],
                "q_type": "matching",
                "ans": [
                    "《小夜曲》 - 莫札特",
                    "《命運交響曲》 - 貝多芬",
                    "《四季》 - 維瓦第",
                    "《天鵝湖》 - 柴可夫斯基"
                ],
                "ai_ans": true,
                "order": 1
            }
        ]
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
          response_schema=list[QuestionGroup],
          system_instruction=instruction
      ),
      contents=message)
  json_data = json.loads(response.text)

  # print(json_data)
  return json_data


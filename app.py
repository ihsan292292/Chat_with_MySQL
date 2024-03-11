import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

load_dotenv()

os.environ['OPENAI_API_KEY'] = os.environ.get("OPENAI_API_KEY")
user = os.environ.get("USER")
password = os.environ.get("PASSWORD")


template = """
Based on the table schema below, write a SQL query that would answer the user's question.
{schema}

Question: {question}
SQL Query:
"""
prompt = ChatPromptTemplate.from_template(template)
prompt.format(schema="my schema",question="how many users are there")

# for mysql
# db_uri = f"mysql+mysqlconnector://{user}:{password}@localhost:3306/chinook"
# db = SQLDatabase.from_uri(db_uri)

# for psql
db_uri = f"postgresql+psycopg2://postgres:password@localhost:5433/crm7"
db = SQLDatabase.from_uri(db_uri)

def get_schema(_):
    return db.get_table_info()

llm = ChatOpenAI()

sql_chain  = (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | llm.bind(stop="\nSQL Result:")
    | StrOutputParser()
)

template = """
Based on the table schema below, question, sql query, and sql response, write a natural language response:
{schema}

Question: {question}
SQL Query: {query}
SQL Response: {response}"""

prompt = ChatPromptTemplate.from_template(template)

def run_query(query):
    return db.run(query)

full_chain =(
    RunnablePassthrough.assign(query = sql_chain).assign(
        schema = get_schema,
        response = lambda vars:run_query(vars["query"])
    )
    | prompt
    | llm
    | StrOutputParser()
)

question = "how many customers are there?"

answer = full_chain.invoke({"question":question})
print("question: how many customers are there?\nanswer:",answer)
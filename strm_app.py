import os
from dotenv import load_dotenv
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

load_dotenv()

# Set your OpenAI API key and other credentials here
os.environ['OPENAI_API_KEY'] = os.environ.get("OPENAI_API_KEY")
user = os.environ.get("USER")
password = os.environ.get("PASSWORD")

# Streamlit app
def main():
    st.title("Chat with Database")

    # Database connection
    db_url = st.text_input("Enter Database URL:")
    st.write(":blue[Example:]")
    p_url = "postgresql+psycopg2://user:password@host(default(localhost)):port(default(5432))/db_name"
    m_url = "mysql+mysqlconnector://user:password@host(default(localhost)):port(default(3306))/db_name"
    st.markdown(f":red[PostgreSQL] : {p_url}")
    st.markdown(f":red[MySQL] : {m_url}")
    if db_url:
        db = SQLDatabase.from_uri(db_url)

        # Get schema
        schema = db.get_table_info()

        # Question input
        question = st.text_input("Enter your SQL question:")

        if st.button("Get Answer"):
            # Chatbot logic
            llm = ChatOpenAI()
            sql_chain = (
                RunnablePassthrough.assign(schema=lambda _: schema)
                | ChatPromptTemplate.from_template("Based on the table schema below, write a SQL query that would answer the user's question.\n{schema}\nQuestion: {question}\nSQL Query:")
                | llm.bind(stop="\nSQL Result:")
                | StrOutputParser()
            )

            # Full chatbot chain
            full_chain = (
                RunnablePassthrough.assign(query=sql_chain).assign(
                    schema=lambda vars: schema,
                    response=lambda vars: db.run(vars["query"])
                )
                | ChatPromptTemplate.from_template("Based on the table schema below, question, SQL query, and SQL response, write a natural language response:\n{schema}\nQuestion: {question}\nSQL Query: {query}\nSQL Response: {response}")
                | llm
                | StrOutputParser()
            )

            # Invoke chatbot
            answer = full_chain.invoke({"question": question})
            st.write("Answer:", answer)

            if st.button("Get Query"):
                llm = ChatOpenAI()
                query = sql_chain.invoke({"question":question})
                st.write("Answer:", query)


if __name__ == "__main__":
    main()
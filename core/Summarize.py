from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
import os

def get_llm():
    return ChatMistralAI(
        model=os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
        api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3
    )

def split_transcript(transcript: str) -> list:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=300,
        length_function=len,
    )
    return text_splitter.split_text(transcript)

def summarize(transcript: str) -> str:
    llm = get_llm()
    chunks = split_transcript(transcript)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a professional meeting summarizer. Create a comprehensive summary of the following meeting transcript.\n"
            "- Identify key decisions made\n"
            "- List major action items and assignees\n"
            "- Note any risks or dependencies\n"
            "- Keep it professional, clear, and concise (1-2 paragraphs)."
        ),
        ("user", "{transcript}"),
    ])

    summarize_chain = {"transcript": RunnablePassthrough()} | prompt | llm | StrOutputParser()

    if len(chunks) <= 1:
        return summarize_chain.invoke(transcript)

    chunk_summaries = [summarize_chain.invoke(chunk) for chunk in chunks]
    combined_transcript = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a professional meeting summarizer. Combine the following chunk summaries into one final professional meeting summary with bullet points."
        ),
        ("user", "{transcript}"),
    ])
    combine_chain = {"transcript": RunnablePassthrough()} | combined_prompt | llm | StrOutputParser()
    return combine_chain.invoke(combined_transcript)

generate_title_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a professional meeting summarizer. Create a creative and interesting title for the following meeting transcript. "
        "Keep it short, interesting, and relevant to the meeting."
    ),
    ("user", "{transcript}"),
])

def get_title(transcript: str) -> str:
    llm = get_llm()
    title_chain = {"transcript": RunnablePassthrough()} | generate_title_prompt | llm | StrOutputParser()
    return title_chain.invoke(transcript)



    



from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.testset.evolutions import simple, reasoning, multi_context
from ragas.testset.generator import TestsetGenerator
from langchain_community.document_loaders import DirectoryLoader
import time
from ragas.run_config import RunConfig
from dotenv import load_dotenv
import asyncio
import argparse

parser = argparse.ArgumentParser(description="Generate synthetic data")
parser.add_argument(
    "--pdf_directory", type=str, help="Path to the directory containing pdfs"
)
parser.add_argument("--num_questions", type=int, help="Number of questions to generate")
args = parser.parse_args()
total_questions = args.num_questions if args.num_questions else 10

load_dotenv()

default_directory = "/home/sonujha/rnd/qp-ai-assessment/data/pdfs/"
pdf_directory = args.pdf_directory if args.pdf_directory else default_directory
print(
    f"Generating {total_questions} questions from all the documents in the directory {pdf_directory}"
)
tik = time.time()
loader = DirectoryLoader(pdf_directory, use_multithreading=True, sample_size=1)
documents = loader.load()
tok = time.time()
print("Loaded {} documents".format(len(documents)))
print("Time taken to load documents: ", tok - tik)

# Add metadata to documents
for document in documents:
    document.metadata["filename"] = document.metadata["source"]


# generator with openai models
generator_llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
critic_llm = ChatOpenAI(model="gpt-4o")
embeddings = OpenAIEmbeddings()

# test the llm
# print(generator_llm("What is the capital of India?"))
# print(critic_llm("What is the capital of India?"))

generator = TestsetGenerator.from_langchain(generator_llm, critic_llm, embeddings)


async def generate_testset():
    return generator.generate_with_langchain_docs(
        documents,
        test_size=total_questions,
        distributions=distributions,
        run_config=RunConfig(),
    )


distributions = {simple: 0.5, reasoning: 0.25, multi_context: 0.25}
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

tik = time.time()
try:
    testset = loop.run_until_complete(generate_testset())
    df = testset.to_pandas()
    file_name = "data/testset.csv"
    df.to_csv(file_name, index=False)
finally:
    # Close the loop
    loop.close()
tok = time.time()
print("Time taken to generate testset: ", tok - tik)

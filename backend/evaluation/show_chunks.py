from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


DOCUMENT_PATH = (
    Path(__file__).resolve().parent.parent
    / "documents"
    / "knowledge_base.txt"
)


loader = TextLoader(
    str(DOCUMENT_PATH),
    encoding="utf-8"
)

documents = loader.load()


splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

chunks = splitter.split_documents(documents)


print(f"Total chunks: {len(chunks)}")


for index, chunk in enumerate(chunks):

    chunk_id = f"kb_{index:03d}"

    print("\n" + "=" * 80)
    print(f"CHUNK ID: {chunk_id}")
    print("=" * 80)
    print(chunk.page_content)
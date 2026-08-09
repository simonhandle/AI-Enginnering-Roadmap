# AI Engineering

Retrieval-Augmented Generation (RAG) kombiniert einen Retriever (findet
relevante Textstücke) mit einem LLM (formuliert die Antwort). Der Retriever
nutzt meist Embeddings und eine Vektor-Suche, um die relevantesten Chunks
aus einer Dokumentensammlung zu finden, bevor sie als Kontext an das LLM
gehen.

Chunking-Strategie beeinflusst die Retrieval-Qualität stark: zu große Chunks
verwässern die Relevanz, zu kleine verlieren Kontext.

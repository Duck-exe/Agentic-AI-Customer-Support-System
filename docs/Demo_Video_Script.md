# Demonstration Video Script

Hello, my name is Dakshanya Maddala. This project is a Multi-Agent AI Customer Support Assistant using Retrieval-Augmented Generation and Large Language Models.

The goal is to improve customer support by using specialized AI agents instead of a single generic chatbot. The system first detects the user's intent and then routes the request to Billing, Technical Support, Product, Complaint, or FAQ agents. It can also invoke multiple agents for a combined problem.

The frontend is built with React. It contains login and registration, a chat window, conversation history, a typing indicator, selected-agent labels, retrieved knowledge sources, response latency, and escalation status.

The backend is built with FastAPI. It provides REST APIs for authentication, chat, conversation history, analytics, and rebuilding the RAG index. Conversations and messages are stored in a database.

For RAG, I created eight fictional TechMart company documents including FAQ, refund, shipping, warranty, pricing, products, installation, and user manual PDFs. The backend extracts and chunks the PDF text, generates sentence-transformer embeddings using all-MiniLM-L6-v2, and stores the vectors in FAISS. The user's question is also embedded so the most relevant company information can be retrieved before generating an answer.

I will first demonstrate individual agents. A duplicate charge question routes to Billing. A login or password issue routes to Technical Support. A pricing comparison routes to Product. A dissatisfied-customer message routes to Complaint. A company-hours question routes to FAQ.

For multi-agent routing, I will ask: "I paid yesterday but Premium is still locked." This contains both payment and access issues, so Billing and Technical agents are selected. Their responses are combined by the response aggregator.

To demonstrate RAG, I will ask: "How long does an approved refund take?" The response is grounded in the refund policy, and I can expand the retrieved sources in the user interface.

Conversation memory is stored by conversation and session ID. I can ask about Premium and then ask a follow-up question without starting a new conversation.

The system also implements human escalation. Low retrieval confidence or an unresolved complaint creates a support ticket and informs the customer that the conversation was flagged for human review.

Finally, I included unit tests and a routing evaluation script, and the database can be switched to PostgreSQL for deployment.

This project demonstrates multi-agent systems, LLM integration, RAG, embeddings, vector databases, REST APIs, full-stack development, conversation memory, database design, testing, and deployment-ready architecture.

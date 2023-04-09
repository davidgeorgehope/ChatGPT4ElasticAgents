import openai
import random
from elasticsearch import Elasticsearch

# Replace with your API key
openai.api_key = "your_openai_api_key_here"

from elasticsearch import Elasticsearch

# Replace with your Elasticsearch credentials and host details
es_username = "your_elasticsearch_username"
es_password = "your_elasticsearch_password"
es_host = "your_elasticsearch_host"
es_port = your_elasticsearch_port

es = Elasticsearch(
    [{"host": es_host, "port": es_port}],
    http_auth=(es_username, es_password),
)

def route_request(user_input, routing_messages, elastic_messages, normal_messages):
    routing_messages.append({"role": "user", "content": user_input})
    routing_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=routing_messages,
    )
    route = routing_response["choices"][0]["content"].strip().lower()
    routing_messages.extend(routing_response["choices"][0]["messages"])

    if route == "elastic_agent":
        return elastic_request(user_input, elastic_messages)
    else:
        return normal_request(user_input, normal_messages)

def elastic_request(user_input, elastic_messages):
    elastic_messages.append({"role": "user", "content": user_input})
    elastic_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=elastic_messages,
    )
    query = elastic_response["choices"][0]["content"].strip()
    elastic_messages.extend(elastic_response["choices"][0]["messages"])

    index_query = f"_index:{index_name} {query}"
    search_results = es.search(body={"query": {"query_string": {"query": index_query}}})

    top_result = search_results["hits"]["hits"][0]["_source"] if search_results["hits"]["hits"] else "No results found."

    # Analyze Elasticsearch result with ChatGPT
    analysis_input = f"Please analyze the following result from Elasticsearch: {top_result}"
    elastic_messages.append({"role": "user", "content": analysis_input})
    analysis_response = openai.ChatCompletion.create(
        model="gpt-4.5-turbo",
        messages=elastic_messages,
    )
    analysis = analysis_response["choices"][0]["content"].strip()
    elastic_messages.extend(analysis_response["choices"][0]["messages"])

    return analysis

def normal_request(user_input, normal_messages):
    normal_messages.append({"role": "user", "content": user_input})
    normal_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=normal_messages,
    )
    reply = normal_response["choices"][0]["content"].strip()
    normal_messages.extend(normal_response["choices"][0]["messages"])

    return reply

if __name__ == "__main__":
    routing_messages = [{"role": "system", "content": "Your job is to simply respond with "elastic_agent" or "normal_agent" and nothing else, no commentary. If any subsequent prompts can be turned into an elastic search query you will respond "elastic_agent" or if you think they cannot you will respond "normal_agent"."}]
    elastic_messages = [{"role": "system", "content": "From this prompt forward I want you to generate elasticsearch queries to help me with my request
Do not provide any commentary just a query"}]
    normal_messages = [{"role": "system", "content": "You are the normal agent, execute chatgpt prompts as normal."}]

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break

        response = route_request(user_input, routing_messages, elastic_messages, normal_messages)
        print("Agent: ", response)



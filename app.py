import openai
import random
import json
from elasticsearch import Elasticsearch

# Replace with your API key
openai.api_key = "your_openai_api_key_here"

from elasticsearch import Elasticsearch

# Replace with your Elasticsearch credentials and host details
from flask import Flask, render_template, request, jsonify
import threading

app = Flask(__name__)

# Initialize variables for Elasticsearch and OpenAI clients
es = None
openai.api_key = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config', methods=['POST'])
def config():
    global es, openai
    openai.api_key = request.form['openai_key']
    es_host = request.form['es_host']
    es_port = int(request.form['es_port'])
    es_username = request.form['es_username']
    es_password = request.form['es_password']

    es = Elasticsearch(
        [{"host": es_host, "port": es_port, "scheme": "https"}],
        http_auth=(es_username, es_password),
    )

    return jsonify({'success': True})

@app.route('/message', methods=['POST'])
def message():
    if not es or not openai.api_key:
        return jsonify({'error': 'Configuration is missing. Please provide the OpenAI API key and Elasticsearch details.'}), 400

    user_input = request.form['user_input']
    response = route_request(user_input, routing_messages, elastic_messages, normal_messages)
    return jsonify({'response': response})

def route_request(user_input, routing_messages, elastic_messages, normal_messages):
    routing_messages.append({"role": "user", "content": user_input})
    routing_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=routing_messages,
    )
    print(routing_response)
    route = routing_response["choices"][0]["message"]["content"].strip().lower()
    #routing_messages.extend(routing_response["choices"][0]["message"])

    if route == "elastic_agent":
        return elastic_request(user_input, elastic_messages)
    else:
        return normal_request(user_input, normal_messages)

def elastic_request(user_input, elastic_messages):
    elastic_messages.append({"role": "user", "content": user_input})
    print(elastic_messages)
    elastic_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=elastic_messages,
    )
    query = elastic_response["choices"][0]["message"]["content"].strip()
    #elastic_messages.extend(elastic_response["choices"][0]["message"])
    print(query)
    json_data = json.loads(query)

    search_results = es.search(body=json_data)

    top_result = search_results["hits"]["hits"][0]["_source"] if search_results["hits"]["hits"] else "No results found."

    # Analyze Elasticsearch result with ChatGPT
    analysis_input = f"Please analyze the following result from Elasticsearch: {top_result}"
    analysis=[{"role": "user", "content": analysis_input}]
    analysis_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=analysis,
    ) 
    print(analysis_response)
    analysis = analysis_response["choices"][0]["message"]["content"].strip()
    #elastic_messages.extend(analysis_response["choices"][0]["message"])

    return analysis

def normal_request(user_input, normal_messages):
    normal_messages.append({"role": "user", "content": user_input})
    normal_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=normal_messages,
    )
    reply = normal_response["choices"][0]["message"]["content"].strip()
    #normal_messages.extend(normal_response["choices"][0]["message"])

    return reply

if __name__ == "__main__":
    routing_messages = [{"role": "system", "content": 'Your job is to simply respond with "elastic_agent" or "normal_agent" and nothing else, no commentary. If any subsequent prompts can be turned into an elastic search query you will respond "elastic_agent" or if you think they cannot you will respond "normal_agent".'}]
    elastic_messages = [{"role": "system", "content": 'From this prompt forward I want you to generate elasticsearch queries to help me with my request. Do not provide any commentary, just a query. Note that the data in here conforms to the Elastic Common Schema standard'}]
    normal_messages = [{"role": "system", "content": "You are the normal agent, execute chatgpt prompts as normal."}]

#    while True:
#        user_input = input("User: ")
#        if user_input.lower() == "exit":
#            break

#        response = route_request(user_input, routing_messages, elastic_messages, normal_messages)
#        print("Agent: ", response)
    app.run(host="localhost", port=8080, debug=True)

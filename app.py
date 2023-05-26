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
        temperature=0,
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
        temperature=0,
    )
    query = elastic_response["choices"][0]["message"]["content"].strip()
    #elastic_messages.extend(elastic_response["choices"][0]["message"])
    print(query)
    json_data = json.loads(query)

    search_results = es.search(body=json_data)
    print(search_results)

    top_result = search_results["hits"]["hits"][0]["_source"] if search_results["hits"]["hits"] else "No results found."

    # Analyze Elasticsearch result with ChatGPT
    analysis_input = f"With the following user input {user_input} Please analyze the following result from Elasticsearch: {top_result}"
    analysis=[{"role": "user", "content": analysis_input}]
    analysis_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=analysis,
        temperature=0,
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
        temperature=0,
    )
    reply = normal_response["choices"][0]["message"]["content"].strip()
    #normal_messages.extend(normal_response["choices"][0]["message"])

    return reply

if __name__ == "__main__":
    routing_messages = [{"role": "system", "content": 'Your job is to simply respond with "elastic_agent" or "normal_agent" and nothing else, no commentary. If any subsequent prompts can be turned into an elastic search query you will respond "elastic_agent" or if you think they cannot you will respond "normal_agent".'}]
    elastic_messages = [{"role": "system", "content": 'From this prompt forward I want you to generate elasticsearch queries to help me with my request. Do not provide any commentary, just a query. here are some example fields that might help you with search _version,_score,fields,host.hostname,process.pid,process_files_open,service.language.name,tomcat_sessions_active_current,tomcat_sessions_rejected,cloud.availability_zone,process_start_time,process.title.text,process_uptime,processor.event,agent.name,host.name,event.agent_id_status,cloud.region,jvm_threads_daemon,tomcat_sessions_active_max,agent.activation_method,processor.name,service.runtime.version,data_stream.type,system_load_average_1m,host.architecture,tomcat_sessions_alive_max,cloud.machine.type,cloud.provider,jvm_threads_peak,observer.version,ecs.version,observer.type,jvm_gc_memory_allocated,agent.version,process.title,jvm_threads_live,jvm_gc_memory_promoted,system_cpu_count,jvm_gc_live_data_size,tomcat_sessions_created,service.node.name,cloud.project.name,system_cpu_usage,cloud.instance.id,host.ip,tomcat_sessions_expired,process_cpu_usage,jvm_classes_unloaded,service.environment,jvm_classes_loaded,service.name,data_stream.namespace,service.runtime.name,observer.hostname,metricset.name,event.ingested,@timestamp,host.os.platform,data_stream.dataset,service.language.version,agent.ephemeral_id,jvm_gc_max_data_size,cloud.instance.name,cloud.project.id,sort,_id,_version,_score,fields,client.geo.country_iso_code,host.hostname,service.language.name,transaction.id,source.ip,http.response.finished,agent.name,event.agent_id_status,http.response.status_code,http.version,user_agent.original,cloud.region,service.runtime.version,host.architecture,cloud.machine.type,cloud.provider,url.path,observer.version,transaction.name,http.request.headers.Upgrade-Insecure-Requests,http.request.headers.Cache-Control,error.exception.type,user_agent.os.full,error.exception.stacktrace.line.number,service.node.name,url.scheme,cloud.project.name,transaction.sampled,user_agent.os.name,error.exception.stacktrace.function,run],host.ip,cloud.instance.id,client.geo.region_name,error.exception.stacktrace.exclude_from_grouping,http.request.headers.User-Agent,service.environment,http.request.headers.Referer,observer.hostname,url.full.text,http.request.headers.Connection,event.ingested,@timestamp,host.os.platform,data_stream.dataset,service.language.version,url.domain,agent.ephemeral_id,error.grouping_name,user_agent.device.name,cloud.project.id,cloud.instance.name,error.exception.message,http.request.headers.Accept,error.exception.stacktrace.filename,process.pid,user_agent.os.version,cloud.availability_zone,process.title.text,http.request.method,http.request.headers.Accept-Language,processor.event,host.name,user_agent.version,client.geo.country_name,processor.name,agent.activation_method,client.ip,user_agent.name,http.request.headers.Host,data_stream.type,timestamp.us,observer.type,ecs.version,error.exception.stacktrace.module,agent.version,parent.id,http.request.headers.Accept-Encoding,process.title,client.geo.continent_name,error.grouping_key,error.exception.stacktrace.library_frame,user_agent.os.name.text,trace.id,client.geo.location,type,url.port,error.exception.stacktrace.classname,url.full,client.geo.city_name,client.geo.region_iso_code,service.name,data_stream.namespace,service.runtime.name,message,transaction.type,user_agent.os.full.text,error.id,highlight,sort'}]
    normal_messages = [{"role": "system", "content": "You are the normal agent, execute chatgpt prompts as normal."}]

    app.run(host="localhost", port=8080, debug=True)

import streamlit as st

from sparql_endpoint_api import SparqlEndpoint
from streamlit_frontend import generate_content, generate_output
from dynamic_query_generation import dynamic_query_generator


def wikidata_movie_browser():
    @st.cache_resource
    def open_connection(url):
        return SparqlEndpoint(url)

    @st.cache_data
    def request_data(_endpoint, query):
        return _endpoint.request(query)

    st.set_page_config(page_title='Wikidata Movie Browser')
    wikidata = open_connection('https://query.wikidata.org/sparql')
    os, ms = generate_content()
    query = dynamic_query_generator(os, ms)
    metadata, data = request_data(wikidata, query)
    generate_output(data, query, os['show_query'])


wikidata_movie_browser()

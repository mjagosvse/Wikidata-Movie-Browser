import streamlit as st
import option_dicts as od
import pandas as pd
from datetime import datetime


def generate_content():
    def generate_output_options():
        os = {}
        with st.sidebar:
            st.title('Output settings')
            os['vars'] = st.multiselect(label='Required attributes', options=(od.VAR_TO_COLNAME_DICT.values()),
                                        default=od.DEFAULT_VAR_DISPLAY)
            os['vars_optional'] = st.multiselect(label='Optional attributes',
                                                 options=([v for v in od.VAR_TO_COLNAME_DICT.values() if v not in os['vars']]),
                                                 help='Attributes will be on output but might contain nulls')
            os['limit'] = st.slider('Output rows', min_value=0, max_value=100, value=10, step=5)
            os['language'] = st.selectbox(
                label='Output language',
                options=('English', 'Czech', 'Slovak', 'German', 'Chinese'),
                index=0
            )
            os['translate_uri'] = st.checkbox(label='Translate URI to labels', value=True)
            os['show_query'] = st.checkbox(label='Show SPARQL query', value=False)

            st.caption('Advanced')
            os['unique_results'] = st.checkbox(label='Guarantee unique results', value=False,
                                               help='(!) Expensive operation, uses GROUP BY, not recommended')
            os['apply_ordering'] = st.checkbox(label='Order results', value=False,
                                               help='(!) Expensive operation, uses ORDER BY, not recommended')
            os['order_by'] = st.selectbox(
                label='Order by',
                options=od.VAR_TO_COLNAME_DICT.values(),
                index=None
            )
            os['order_dir'] = st.selectbox(
                label='Order direction',
                options=('Ascending', 'Descending'),
                index=0
            )

        return os

    def generate_movie_selection():
        ms = {}

        st.header('Movie selection')
        ms['Title'] = st.text_input(label='Title')
        ms['Genre'] = st.selectbox(label='Genre', options=od.GENRE_DICT, index=None)
        ms['Language'] = st.selectbox(label='Language', options=od.LANGUAGE_DICT, index=None)
        release_year_slider = st.select_slider(label='Release Year',
                                               options=tuple(range(1900, datetime.now().year + 1)),
                                               value=(1900, datetime.now().year))
        ms['Release Date'] = release_year_slider if release_year_slider != (1900, datetime.now().year) else None

        with st.expander('Casting Information', expanded=False):
            ms['Director'] = st.text_input(label='Director')
            ms['Cast Member'] = st.text_input(label='Cast Member')
            ms['Filming Location'] = st.text_input(label='Filming Location')
            ms['Characters'] = st.text_input(label='Characters')

        with st.expander('Miscellaneous'):
            duration_slider = st.select_slider(label='Duration (minutes)', options=tuple(range(0, 242)),
                                               value=(0, 241))
            ms['Duration (minutes)'] = duration_slider if duration_slider != (0, 241) else None
            rating_slider = st.select_slider(label='Rating', options=tuple(range(0, 101)),
                                             value=(0, 100))
            ms['Rating'] = rating_slider if rating_slider != (0, 100) else None
            ms['Website'] = st.text_input(label='Website')
            ms['Award Received'] = st.text_input(label='Award Received')

        return ms

    os = generate_output_options()
    ms = generate_movie_selection()

    return os, ms


def generate_output(data, query, show_query):
    def get_df_from_resp(data):
        new_data = []
        for r in data:
            parsed_dict = {}
            for k, v in r.items():
                parsed_dict[k] = v['value']

            new_data.append(parsed_dict)

        # Sort and rename cols
        df = pd.DataFrame(new_data)
        df = df.rename(
            columns={c: od.VAR_TO_COLNAME_DICT['?' + c.replace('_out', '').replace('_label', '')] for c in df.columns}
        )
        return df[sorted(df.columns, key=lambda c: od.COL_ORDER_DICT[c])]

    def display_results(df, query, show_query):
        if show_query:
            st.caption('Query')
            st.code(query)

        st.caption('Results')
        st.dataframe(df)

    df = get_df_from_resp(data)
    display_results(df, query, show_query)

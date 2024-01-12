import option_dicts as od
import streamlit as st

def dynamic_query_generator(os, ms):
    def construct_query(os, mdef):
        select = '\n\t'.join([c['select_statement'] for c in mdef.values() if c['select_statement']])
        where = ' .\n\t'.join([c['where_statement'] for c in mdef.values() if c['where_statement']])
        label = ' .\n\t'.join([c['label_statement'] for c in mdef.values() if c['label_statement']])
        filter = ' .\n\t'.join([c['filter_condition'] for c in mdef.values() if c['filter_condition']])
        formatting = ' .\n\t'.join([c['formatting_condition'] for c in mdef.values() if c['formatting_condition']])
        limit = os['limit']
        apply_ordering = os['apply_ordering']
        order_by = os['order_by']
        order_dir = os['order_dir']
        unique_results = os['unique_results']

        return f'''
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT 
        {select}
WHERE {{ 
        ?movie wdt:P31 wd:Q11424 . 

        # Define variables
        {where + ' .' if where else ''}

        # Get labels
        {label + ' .' if label else ''}

        # Apply user filters
        {filter + ' .' if filter else ''}

        # Apply formatting filters
        {formatting + ' .' if formatting else ''} 
}}
{'GROUP BY ?title' if unique_results else ''}
{'ORDER BY ' + od.ORDER_DIR_DICT[order_dir] + '(' + {v: k for k, v in od.VAR_TO_COLNAME_DICT.items()}[order_by] + ')'
    if order_by and apply_ordering else ''}
LIMIT {limit}
            '''

    def construct_movie_definition(os, ms):
        def get_select_component(var, aggregate=True, is_label=False):
            if od.VAR_TO_COLNAME_DICT[var] not in out_vars + out_vars_optional:
                return None

            var = var if not is_label else var + '_label'
            if unique_results and aggregate:
                return '(SAMPLE(' + var + ') as ' + var.replace('_label', '') + '_out)'
            else:
                return f'({var} as {var}_out)'

        def get_where_component(var, val, predicate, optional=True):
            if od.VAR_TO_COLNAME_DICT[var] not in out_vars + out_vars_optional and not val:
                return None

            if optional:
                return f'OPTIONAL{{?movie {predicate} {var}}}'
            else:
                return f'?movie {predicate} {var}'

        def get_label_component(var, val, binding_function=None):
            if od.VAR_TO_COLNAME_DICT[var] not in out_vars + out_vars_optional and not val:
                return None
            elif binding_function:
                return f'{binding_function} as {var}_label)'
            else:
                return f'{var} rdfs:label {var}_label'

        def get_filter_component(var, val, cond_type, options_dict=None, is_label=False):
            if not val:
                return None

            var = var if not is_label else var + '_label'
            if cond_type == 'contains':
                return f'FILTER(CONTAINS({var}, "{val}"))'
            elif cond_type == 'equals':
                return f'FILTER({var} = {options_dict[val]})'
            elif cond_type == 'in_range':
                return f'FILTER({var} >= {val[0]} && {var} <= {val[1]})'

        def get_formatting_component(var, val, format_type, pattern=None, is_label=False):
            if od.VAR_TO_COLNAME_DICT[var] not in out_vars + out_vars_optional and not val:
                return None

            var = var if not is_label else var + '_label'
            if format_type == 'language':
                return f'FILTER(LANG({var}) = "{od.LABEL_LANGUAGE_DICT[out_language]}")'
            elif format_type == 'regex':
                return f'FILTER(REGEX({var}, "{pattern}"))'

        # st.write(os)
        out_language = os['language']
        out_vars = os['vars']
        out_vars_optional = os['vars_optional']
        unique_results = os['unique_results']
        translate_uri = os['translate_uri']

        mdef = {
            'Title': {
                'select_statement': get_select_component('?title', aggregate=False),
                'where_statement': get_where_component('?title', ms['Title'], 'rdfs:label', optional='Title' in out_vars_optional),
                'label_statement': None,
                'filter_condition': get_filter_component('?title', ms['Title'], 'contains'),
                'formatting_condition': get_formatting_component('?title', ms['Title'], 'language')
            },
            'Genre': {
                'select_statement': get_select_component('?genre', is_label=translate_uri),
                'where_statement': get_where_component('?genre', ms['Genre'], 'wdt:P136', optional='Genre' in out_vars_optional),
                'label_statement': get_label_component('?genre', ms['Genre']),
                'filter_condition': get_filter_component('?genre', ms['Genre'], 'equals', od.GENRE_DICT),
                'formatting_condition': get_formatting_component('?genre', ms['Genre'], 'language', is_label=True)
            },
            'Language': {
                'select_statement': get_select_component('?language', is_label=translate_uri),
                'where_statement': get_where_component('?language', ms['Language'], 'wdt:P364', optional='Language' in out_vars_optional),
                'label_statement': get_label_component('?language', ms['Language']),
                'filter_condition': get_filter_component('?language', ms['Language'], 'equals', od.LANGUAGE_DICT),
                'formatting_condition': get_formatting_component('?language', ms['Language'], 'language', is_label=True)
            },
            'Release Date': {
                'select_statement': get_select_component('?release_date'),
                'where_statement': get_where_component('?release_date', ms['Release Date'], 'wdt:P577', optional=False),
                'label_statement': None,
                'filter_condition': get_filter_component('year(?release_date)', ms['Release Date'], 'in_range'),
                'formatting_condition': None
            },
            'Rating': {
                'select_statement': get_select_component('?rating'),
                'where_statement': get_where_component('?rating', ms['Rating'], 'wdt:P444', optional='Rating' in out_vars_optional),
                'label_statement': get_label_component('?rating', ms['Rating'], 'BIND (xsd:integer(REPLACE(?rating, "/100", ""))'),
                'filter_condition': get_filter_component('?rating', ms['Rating'], 'in_range', is_label=True),
                'formatting_condition': get_formatting_component('?rating', ms['Rating'], 'regex', pattern='^[0-9]{1,3}/100$')
            },
            'Director': {
                'select_statement': get_select_component('?director', is_label=translate_uri),
                'where_statement': get_where_component('?director', ms['Director'], 'wdt:P57', optional='Director' in out_vars_optional),
                'label_statement': get_label_component('?director', ms['Director']),
                'filter_condition': get_filter_component('?director', ms['Director'], 'contains', is_label=True),
                'formatting_condition': get_formatting_component('?director', ms['Director'], 'language', is_label=True)
            },
            'Filming Location': {
                'select_statement': get_select_component('?filming_location', is_label=translate_uri),
                'where_statement': get_where_component('?filming_location', ms['Filming Location'], 'wdt:P915', optional='Filming Location' in out_vars_optional),
                'label_statement': get_label_component('?filming_location', ms['Filming Location']),
                'filter_condition': get_filter_component('?filming_location', ms['Filming Location'], 'contains', is_label=True),
                'formatting_condition': get_formatting_component('?filming_location', ms['Filming Location'], 'language', is_label=True)
            },
            'Award Received': {
                'select_statement': get_select_component('?award_received', is_label=translate_uri),
                'where_statement': get_where_component('?award_received', ms['Award Received'], 'wdt:P166', optional='Award Received' in out_vars_optional),
                'label_statement': get_label_component('?award_received', ms['Award Received']),
                'filter_condition': get_filter_component('?award_received', ms['Award Received'], 'contains', is_label=True),
                'formatting_condition': get_formatting_component('?award_received', ms['Award Received'], 'language', is_label=True)
            },
            'Characters': {
                'select_statement': get_select_component('?characters', is_label=translate_uri),
                'where_statement': get_where_component('?characters', ms['Characters'], 'wdt:P674', optional='Characters' in out_vars_optional),
                'label_statement': get_label_component('?characters', ms['Characters']),
                'filter_condition': get_filter_component('?characters', ms['Characters'], 'contains', is_label=True),
                'formatting_condition': get_formatting_component('?characters', ms['Characters'], 'language', is_label=True)
            },
            'Cast Member': {
                'select_statement': get_select_component('?cast_member', is_label=translate_uri),
                'where_statement': get_where_component('?cast_member', ms['Cast Member'], 'wdt:P161',
                                                       optional='Cast Member' in out_vars_optional),
                'label_statement': get_label_component('?cast_member', ms['Cast Member']),
                'filter_condition': get_filter_component('?cast_member', ms['Cast Member'], 'contains', is_label=True),
                'formatting_condition': get_formatting_component('?cast_member', ms['Cast Member'], 'language',
                                                                 is_label=True)
            },
            'Website': {
                'select_statement': get_select_component('?website'),
                'where_statement': get_where_component('?website', ms['Website'], 'wdt:P856', optional='Website' in out_vars_optional),
                'label_statement': None,
                'filter_condition': get_filter_component('?website', ms['Website'], 'contains', is_label=False),
                'formatting_condition': None
            },
            'Duration (minutes)': {
                'select_statement': get_select_component('?duration'),
                'where_statement': get_where_component('?duration', ms['Duration (minutes)'], 'wdt:P2047', optional='Duration (minutes)' in out_vars_optional),
                'label_statement': None,
                'filter_condition': get_filter_component('?duration', ms['Duration (minutes)'], 'in_range', is_label=False),
                'formatting_condition': None
            },
            'Cost': {
                'select_statement': get_select_component('?cost'),
                'where_statement': get_where_component('?cost', None, 'wdt:P2130', optional='Cost' in out_vars_optional),
                'label_statement': None,
                'filter_condition': None,
                'formatting_condition': None
            },
            'Box Office': {
                'select_statement': get_select_component('?box_office'),
                'where_statement': get_where_component('?box_office', None, 'wdt:P2142', optional='Box Office' in out_vars_optional),
                'label_statement': None,
                'filter_condition': None,
                'formatting_condition': None
            },
            'CSFD Film ID': {
                'select_statement': get_select_component('?csdf_filmid'),
                'where_statement': get_where_component('?csdf_filmid', None, 'wdt:P2529', optional='CSFD Film ID' in out_vars_optional),
                'label_statement': None,
                'filter_condition': None,
                'formatting_condition': None
            },

        }

        return mdef

    # st.write(os)
    mdef = construct_movie_definition(os, ms)
    return construct_query(os, mdef)




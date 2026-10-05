import os
import streamlit as st
import psycopg
from psycopg.rows import dict_row
from elasticsearch import Elasticsearch
st.set_page_config(page_title='Job Market Explorer',layout='wide')
st.title('Job Market Explorer')
st.caption('Historical job metadata snapshot • Title and department search • No salary or skill data')

@st.cache_resource
def elastic(): return Elasticsearch(os.environ['ELASTIC_URL'])
def query(sql):
    with psycopg.connect(os.environ['POSTGRES_DSN'], row_factory=dict_row) as conn:
        return conn.execute(sql).fetchall()

search,analytics=st.tabs(['Search','Analytics'])
with search:
    countries=['All']+[r['country'] for r in query('SELECT DISTINCT country FROM jobs WHERE country IS NOT NULL ORDER BY country')]
    with st.form('search'):
        text=st.text_input('Job title or department',placeholder='data engineer')
        a,b,c=st.columns(3)
        country=a.selectbox('Country',countries)
        status=b.selectbox('Source status',['All','active','closed'])
        remote=c.checkbox('Remote only')
        submitted=st.form_submit_button('Search')
    if submitted:
        filters=[]
        if country!='All': filters.append({'term':{'country':country}})
        if status!='All': filters.append({'term':{'status':status}})
        if remote: filters.append({'term':{'is_remote':True}})
        must={'multi_match':{'query':text,'fields':['title^3','department'],'fuzziness':'AUTO'}} if text.strip() else {'match_all':{}}
        result=elastic().search(index='jobs',query={'bool':{'must':[must],'filter':filters}},size=50,track_total_hits=True)
        st.write(f"{result['hits']['total']['value']:,} matches; showing up to 50")
        for hit in result['hits']['hits']:
            r=hit['_source']
            with st.container(border=True):
                st.subheader(r['title'])
                st.write(f"{r.get('country') or 'Unknown country'} · {r.get('workplace_type') or 'Unknown workplace'} · {r.get('status') or 'Unknown status'}")
                st.caption(f"Company ID: {r['company_id']} | Posted: {r.get('posted_at') or 'Unknown'}")
                if r.get('apply_url'): st.link_button('Original posting (may be closed)',r['apply_url'])
with analytics:
    st.warning('This snapshot is not a representative survey of the labor market. Dates and statuses reflect the source; closed postings remain searchable.')
    totals=query('SELECT COUNT(*) AS postings,COUNT(DISTINCT company_id) AS companies,SUM(is_remote::int) AS remote FROM jobs')[0]
    for col,(key,val) in zip(st.columns(3),totals.items()): col.metric(key.title(),val or 0)
    st.subheader('Postings by country')
    data=query("SELECT COALESCE(country,'Unknown') AS country,COUNT(*) AS postings FROM jobs GROUP BY country ORDER BY postings DESC LIMIT 15")
    st.bar_chart(data, x='country', y='postings')
    st.subheader('Monthly posting volume')
    st.dataframe(query("SELECT date_trunc('month',posted_at) AS month,COUNT(*) AS postings FROM jobs WHERE posted_at IS NOT NULL GROUP BY month ORDER BY month"))
    st.subheader('Employment types')
    st.dataframe(query('SELECT employment_type,COUNT(*) AS postings FROM jobs GROUP BY employment_type ORDER BY postings DESC'))

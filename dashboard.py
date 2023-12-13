import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import plotly.subplots as sp

st.header('Dashboard E-Commerce Public Dataset')
#IMPORT DATA
df_order_item = pd.read_csv('olist_order_items_dataset.csv')
df_order_payment = pd.read_csv('olist_order_payments_dataset.csv')
df_product = pd.read_csv('olist_products_dataset.csv')
df_product_cat = pd.read_csv('product_category_name_translation.csv')
df_seller = pd.read_csv('olist_sellers_dataset.csv')
df_customer = pd.read_csv('olist_customers_dataset.csv')
df_review = pd.read_csv('olist_order_reviews_dataset.csv')
df_delivery = pd.read_csv('olist_orders_dataset.csv')
#DATA PREPARATION
##PRODUCT
df_order_price = df_order_item.merge(df_order_payment, how='inner', on='order_id').sort_values(by='order_id')
df_product_category = df_product.merge(df_product_cat, on='product_category_name', how='inner')[['product_id', 'product_category_name_english']]
df_order_product = df_order_price.merge(df_product_category, on='product_id', how='inner').groupby(by=['order_id', 'product_id', 'product_category_name_english'], as_index=False).sum()
##TIMESTAMP
df_customer = df_customer[['customer_id', 'customer_unique_id', 'customer_city', 'customer_state']]
df_review = df_review[['review_id', 'order_id', 'review_score']]
cols = df_delivery.columns[3:]
df_delivery[cols] = df_delivery[cols].apply(pd.to_datetime, errors='coerce')
###duration from order to arrive at customer
df_delivery['duration_arrived'] = (df_delivery['order_delivered_customer_date']-df_delivery['order_purchase_timestamp']).dt.days
###duration from carrier to arrive at customer
df_delivery['duration_carrier_customer'] = (df_delivery['order_delivered_customer_date']-df_delivery['order_delivered_carrier_date']).dt.days
###duration from purchase to arrive at carrier
df_delivery['duration_customer_carrier'] = (df_delivery['order_delivered_carrier_date']-df_delivery['order_purchase_timestamp']).dt.days
###difference of estimated time to duration_arrived
df_delivery['estimated_qos'] = (df_delivery['order_estimated_delivery_date']-df_delivery['order_delivered_customer_date']).dt.days
df_timestamp = df_delivery.iloc[:,[0,1,2,3,8,9,10,11]].sort_values('order_purchase_timestamp').reset_index(drop=True)
###drop NA - for 'delivered' status only in duration
df_timestamp = df_timestamp.dropna()
####finding anomalies in duration_arrived
q1 = np.percentile(df_timestamp['duration_arrived'], 25)
q3 = np.percentile(df_timestamp['duration_arrived'], 75)
####threshold iqr
iqr = q3-q1
iqr_anomaly = 1.5*iqr
####threshold data q1 & q3
q1_anomaly = q1-iqr_anomaly
q3_anomaly = q3+iqr_anomaly
####drop outlier (outside threshold q1 & q3)
df_timestamp = df_timestamp[(df_timestamp['duration_arrived']>q1_anomaly) | (df_timestamp['duration_arrived']<q3_anomaly)].reset_index(drop=True)
df_timestamp = df_timestamp[df_timestamp['order_status']=='delivered']
df_timestamp['order_date'] = df_timestamp['order_purchase_timestamp'].dt.date

#SIDEBAR CHOOSE DATE---------------------------------------
min_date = df_timestamp['order_date'].min()
max_date = df_timestamp['order_date'].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://github.com/salmanzf/Brazil-Ecommerce-Public-Dataset/blob/streamlit/kisspng-mobile-app-application-software-e-commerce-vector-vector-online-shopping-5aa2ad8b6127c4.393135701520610699398.png?raw=true")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

df_timestamp = df_timestamp[(df_timestamp['order_date']>=start_date) & (df_timestamp['order_date']<=end_date)]

#GENERATED REVENUE
st.subheader('Daily Order')
df_time_price = df_timestamp.merge(df_order_product, on='order_id', how='inner')
col1, col2 = st.columns(2)
with col1:
    total_orders = df_time_price['order_id'].nunique()
    st.metric("Total Order", value=total_orders)
 
with col2:
    total_revenue = df_time_price['payment_value'].sum()
    st.metric("Total Revenue", value=total_revenue)

line_time_price = df_time_price.groupby('order_date', as_index=False)['order_id'].nunique()
fig0 = px.line(line_time_price,
               x="order_date",
               y="order_id",
               labels={
                'order_date':'Date',
                'order_id':'Total Order'})
fig0.update_layout(coloraxis_showscale=False
    )
st.plotly_chart(fig0)

#GENERATED REVENUE BY PRODUCT
df_revenue_product = df_time_price.groupby('product_category_name_english', as_index=False)['payment_value'].sum().sort_values('payment_value', ascending=False).reset_index(drop=True)
labels1 = round(df_revenue_product['payment_value']/1E3, 2).head(10).astype('str') + 'K'
labels2 = round(df_revenue_product['payment_value']/1E3, 2).tail(10).astype('str') + 'K'
st.subheader('Generated Revenue by Product')
col1, col2 = st.columns(2)
with col1:
    fig1 = px.bar(df_revenue_product.head(10), x="payment_value", y="product_category_name_english",
              color="payment_value",
              labels={
                'payment_value':'Revenue',
                'product_category_name_english':'Product Category'},
               color_continuous_scale=px.colors.sequential.tempo,
               text=labels1)
    fig1.update_layout(height = 500,
                       width = 1200,
                       title_text = "Most Generated Revenues by Product",
                       title={
                              'x':0.6,
                              'y':1
                              },
                       title_font_size = 20,
                       yaxis=dict(
                       autorange='reversed'
                        ),
                       coloraxis_showscale=False
    )
    st.plotly_chart(fig1)
with col2:
    fig2 = px.bar(df_revenue_product.tail(10), x="payment_value", y="product_category_name_english",
              color="payment_value",
              labels={
                'payment_value':'Revenue',
                'product_category_name_english':'Product Category'},
               color_continuous_scale=px.colors.sequential.tempo,
               text=labels2)
    fig2.update_layout(height = 500,
                       width = 1200,
                       title_text = "Least Generated Revenues Product",
                       title={
                              'x':0.6,
                              'y':1
                              },
                       title_font_size = 20,
                       coloraxis_showscale=False
    )
    st.plotly_chart(fig2)

#MOST & LEAST GENERATED REVENUE REGION----------------------------------
st.subheader('Generated Revenue by State & City')
revenue_area = df_time_price.merge(df_customer, on='customer_id', how='inner')
tab1, tab2 = st.tabs(["State", "City"])
with tab1:
    revenue_area_state = revenue_area.groupby('customer_state', as_index=False)['payment_value'].sum().sort_values('payment_value', ascending=False)
    revenue_area_state['percentage'] = (revenue_area_state['payment_value']/revenue_area_state['payment_value'].sum())*100
    labels = round(revenue_area_state['payment_value'].head(10)/1E6, 2).astype('str') + 'M'
    col1, col2 = st.columns(2)
    with col1:
        fig3 = px.bar(revenue_area_state.head(10), x="payment_value", y="customer_state",
              color="payment_value",
              labels={
                'payment_value':'Revenue',
                'customer_state':'State'},
               color_continuous_scale=px.colors.sequential.tempo,
               text=labels
               )
        fig3.update_layout(margin=dict(l=20, r=0, t=20, b=0),
                           title_text = "Most Generated Revenues State",
                           title={
                              'x':0.6,
                              'y':1
                              },
                            yaxis=dict(
                            autorange='reversed'
                            ),
                           title_font_size = 20,
                           coloraxis_showscale=False
                           )
        st.plotly_chart(fig3)
    with col2:
        top_5 = revenue_area_state[:5]
        new_row = pd.DataFrame(data={
                'customer_state':['Others'],
                'payment_value':[revenue_area_state['payment_value'][5:].sum()],
                'percentage':[revenue_area_state['percentage'][5:].sum()]
        })
        pie_revenue_state = pd.concat([top_5, new_row]).reset_index(drop=True)
        fig4 = px.pie(pie_revenue_state,
                          values='payment_value',
                          names='customer_state',
                          color_discrete_sequence=px.colors.qualitative.Antique)
        fig4.update_traces(sort=False)
        fig4.update_layout(margin=dict(l=20, r=0, t=20, b=0),
                           title_text = "Generated Revenues by State (%)",
                           title={
                              'x':0.5,
                              'y':1
                              },
                           title_font_size = 20
            )
        st.plotly_chart(fig4)
with tab2:
    revenue_area_city = revenue_area.groupby(['customer_city','customer_state'], as_index=False)['payment_value'].sum().sort_values('payment_value', ascending=False).reset_index(drop=True)
    revenue_area_city['percentage'] = round((revenue_area_city['payment_value']/revenue_area_city['payment_value'].sum())*100, 2)
    labels = round(revenue_area_city['payment_value'].head(10)/1E6, 2).astype('str') + 'M'
    col1, col2 = st.columns(2)
    with col1:
        fig5 = px.bar(revenue_area_city.head(10), x="payment_value", y="customer_city",
              color="customer_state",
              labels={
                'payment_value':'Revenue',
                'customer_city':'City'},
               color_discrete_sequence=px.colors.qualitative.Vivid,
               text=labels
               )
        fig5.update_layout(margin=dict(l=20, r=0, t=20, b=0),
                           title_text = "Most Generated Revenues City",
                           title={
                              'x':0.6,
                              'y':1
                              },
                            yaxis=dict(
                            categoryorder='total ascending'
                            ),
                           title_font_size = 20
                           )
        st.plotly_chart(fig5)
    with col2:
        top_5 = revenue_area_city[:5]
        new_row = pd.DataFrame(data={
                'customer_city':['Others'],
                'payment_value':[revenue_area_city['payment_value'][5:].sum()],
                'percentage':[revenue_area_city['percentage'][5:].sum()]
        })
        pie_revenue_city = pd.concat([top_5, new_row]).reset_index(drop=True)
        fig6 = px.pie(pie_revenue_city,
                          values='payment_value',
                          names='customer_city',
                          color_discrete_sequence=px.colors.qualitative.Antique)
        fig6.update_traces(sort=False)
        fig6.update_layout(margin=dict(l=20, r=0, t=20, b=0),
                           title_text = "Generated Revenues by City (%)",
                           title={
                              'x':0.5,
                              'y':1
                              },
                           title_font_size = 20
            )
        st.plotly_chart(fig6)




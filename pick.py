# pick.py
import streamlit as st
import pandas as pd
import numpy as np
import io
import base64

def pick_page():
    def get_binary_file_downloader_html(bin_file, file_label='File'):
        bin_str = base64.b64encode(bin_file).decode()
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">Download {file_label}</a>'
        return href

    uploaded_file_csv = st.file_uploader("CSVファイルをアップロード", type="csv")
    uploaded_file_excel = st.file_uploader("Excelファイルをアップロード", type="xlsx")

    if uploaded_file_csv is not None and uploaded_file_excel is not None:
        df = pd.read_csv(uploaded_file_csv, encoding='shift_jis')
        df.rename(columns={'在庫ID': 'Product Code', '数量': 'Quantity'}, inplace=True)
        df['Product Code'] = df['Product Code'].astype(str)
        df['Quantity'] = df['Quantity'].astype(int)

        # 在庫コードごとに数量の合計を計算
        quantity_sum = df.groupby('Product Code')['Quantity'].sum().reset_index()

        inventory_df = pd.read_excel(uploaded_file_excel, usecols='C')
        inventory_df.columns = ['在庫コード']
        inventory_df['在庫コード'] = inventory_df['在庫コード'].astype(str)

        # 在庫コードで結合し、最初に現れる行のみに数量を表示
        merged_df = pd.merge(inventory_df, quantity_sum, left_on='在庫コード', right_on='Product Code', how='left')
        merged_df.drop('Product Code', axis=1, inplace=True)
        merged_df['first_appearance'] = merged_df.duplicated('在庫コード')
        merged_df['Quantity'] = merged_df.apply(lambda x: x['Quantity'] if not x['first_appearance'] else np.nan, axis=1)
        merged_df.drop('first_appearance', axis=1, inplace=True)

        # 一致しなかった在庫コードと数量を抽出
        unmatched_df = df[~df['Product Code'].isin(inventory_df['在庫コード'])]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            merged_df.to_excel(writer, sheet_name='Sheet1', index=False)

        binary_excel = output.getvalue()  
        st.markdown(get_binary_file_downloader_html(binary_excel, 'Merged_YourFileNameHere.xlsx'), unsafe_allow_html=True)

        # 一致しなかった在庫コードと数量を表示
        if not unmatched_df.empty:
            st.write("CSVファイル内でExcelファイルと一致しなかった在庫コードと数量:")
            st.write(unmatched_df[['Product Code', 'Quantity']])

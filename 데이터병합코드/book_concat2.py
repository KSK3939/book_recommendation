import pandas as pd

df = pd.read_csv('../data_나라/yes24_steadyseller_영미.csv')
df['국가'] = '영미'

df_temp = pd.read_csv('../data_나라/yes24_steadyseller_일본.csv')
df_temp['국가'] = '일본'
df=pd.concat([df_temp, df],ignore_index=True)

df_temp = pd.read_csv('../data_나라/yes24_steadyseller_한국.csv')
df_temp['국가'] = '한국'
df=pd.concat([df_temp, df],ignore_index=True)

df_temp = pd.read_csv('../data_나라/원본데이터/yes24_steadyseller_독일.csv')
df_temp['국가'] = '독일'
df=pd.concat([df_temp, df],ignore_index=True)

df_temp = pd.read_csv('../data_나라/원본데이터/yes24_steadyseller_러시아.csv')
df_temp['국가'] = '러시아'
df=pd.concat([df_temp, df],ignore_index=True)


df_temp = pd.read_csv('../data_나라/원본데이터/yes24_steadyseller_중국.csv')
df_temp['국가'] = '중국'
df=pd.concat([df_temp, df],ignore_index=True)

df_temp = pd.read_csv('../data_나라/원본데이터/yes24_steadyseller_프랑스.csv')
df_temp['국가'] = '프랑스'
df=pd.concat([df_temp, df],ignore_index=True)

df = df[['ISBN','상품명', '저자', '출판사', '설명','국가']]
df['ISBN'] = df['ISBN'].astype('Int64')

df.info()
df.to_csv('data/yes24_steadyseller_국가.csv', index=False)

from codecs import ignore_errors

import pandas as pd

df = pd.read_csv('data_나라/yes24_steadyseller_영미.csv')
print(df.head())


df['국가'] = '영미'

df_temp = pd.read_csv('data_나라/yes24_steadyseller_일본.csv')
df_temp['국가'] = '일본'
df=pd.concat([df_temp, df],ignore_index=True)


df_temp = pd.read_csv('data_나라/yes24_steadyseller_한국.csv')
df_temp['국가'] = '한국'

df=pd.concat([df_temp, df],ignore_index=True)
print(df.head())

df = df.drop_duplicates()

df = df[['ISBN','국가']]
df['ISBN'] = df['ISBN'].astype('Int64')


df_temp = pd.read_csv('data_나라/yes24_steadyseller_독일_정리.csv')
df=pd.concat([df_temp, df],ignore_index=True)


df_temp = pd.read_csv('data_나라/yes24_steadyseller_중국_정리.csv')
df=pd.concat([df_temp, df],ignore_index=True)

df_temp = pd.read_csv('data_나라/yes24_steadyseller_러시아_정리.csv')
df=pd.concat([df_temp, df],ignore_index=True)

df_temp = pd.read_csv('data_나라/yes24_steadyseller_프랑스_정리.csv')
df=pd.concat([df_temp, df],ignore_index=True)

print(df.head())

df.info()
df.to_csv('data/yes24_steadyseller_국가통합.csv', index=False)

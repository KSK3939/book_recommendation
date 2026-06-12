import pandas as pd
df = pd.read_csv('../data/yes24_steadyseller_장르통합.csv')
df = df[['ISBN','장르']]
df['ISBN'] = df['ISBN'].astype('Int64')

df.info()
df.to_csv('data/yes24_steadyseller_장르.csv', index=False)
import pandas as pd

# 독일
# df = pd.read_csv('data_나라/yes24_steadyseller_독일.csv')
#
# df = df.dropna(subset=['설명'])
# df = pd.DataFrame(df['ISBN'])
# df['국가'] = '독일'
# df.to_csv('data_나라/yes24_steadyseller_독일_정리.csv', index=False, encoding='utf-8-sig')

# # 중국
# df = pd.read_csv('data_나라/yes24_steadyseller_중국.csv')
#
# df = df.dropna(subset=['설명'])
# df = pd.DataFrame(df['ISBN'])
# df['국가'] = '중국'
# df.to_csv('data_나라/yes24_steadyseller_중국_정리.csv', index=False, encoding='utf-8-sig')


# # 러시아
# df = pd.read_csv('data_나라/yes24_steadyseller_러시아.csv')
#
# df = df.dropna(subset=['설명'])
# df = pd.DataFrame(df['ISBN'])
# df['국가'] = '러시아'
# df.to_csv('data_나라/yes24_steadyseller_러시아_정리.csv', index=False, encoding='utf-8-sig')

# 프랑스
df = pd.read_csv('../data_나라/원본데이터/yes24_steadyseller_프랑스.csv')

df = df.dropna(subset=['설명'])
df = pd.DataFrame(df['ISBN'])
df['국가'] = '프랑스'
df.to_csv('data_나라/yes24_steadyseller_프랑스_정리.csv', index=False, encoding='utf-8-sig')


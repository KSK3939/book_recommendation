import pandas as pd
from wordcloud import WordCloud
import collections
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

font_path = './malgun.ttf'
font_name = font_manager.FontProperties(fname = font_path).get_name()
plt.rc('font', family = 'NanumBarunGothic')

df = pd.read_csv('./data/final_merge_preprocessed.csv')
book_index = 4397
words = str(df.loc[book_index, '설명']).split()
print(df.loc[book_index, '제목'])

worddict = collections.Counter(words)
worddict = dict(worddict)
print(worddict)

wordcloud = WordCloud(font_path = font_path, background_color='white',).generate_from_frequencies(worddict)
plt.imshow(wordcloud)
plt.axis("off")
plt.show()
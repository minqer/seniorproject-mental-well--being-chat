# -*- encoding: utf-8 -*-

import codecs
import string
import sys
from collections import defaultdict

from sys import argv
from sklearn.externals import joblib
from sklearn.feature_extraction.text import TfidfTransformer
from word_segmentation_lexto import Tws
from pgdb_data import DB

def custom_preprocessor(str):
    # Do not perform any preprocessing here.
    return str

def custom_tokenizer(str):
    # Text must be segmented and separated each word by a space.
    return str.split(' ')

if len(argv) < 4:
    print "Usage: predict.py <count_vectorizer_path> <model_path> <text ID> [text ID,...]"
    sys.exit()

count_vec_path = argv[1]
model_path = argv[2]

# load models
count_vec = joblib.load(count_vec_path)
clf = joblib.load(model_path)

# preprocessing steps
text_ids = argv[3:]
text = []

db = DB()
for id in text_ids:
    ids = id.split('-')
    content = db.get_paragraph_text(ids[0],ids[1])

    if content:
        text.append(content)

# load dicts
tws = Tws()
stopwords = codecs.open('dicts/stop_words.txt', 'r','utf-8').read().split()
lemma_dict = dict()
with open('dicts/lemma_dict','r') as f:
    for line in f:
        lemma,words = line.split(":")
        for word in words.split(","):
            word = word.strip()
            lemma_dict[unicode(word,'utf-8')] = lemma

final_text = []
short_parageaph = []

# perform real preprocessing
for i in range(0,len(text)):
    if not text[i]:
        continue
        
    filteredtext = []
    tmp_text = tws.word_segment(unicode(text[i].strip(),'utf-8'))

    # preprocess
    for t in tmp_text:
        t = t.strip()
        
        # remove punctuation
        t = t.translate({ord(char): None for char in (string.punctuation + unicode('‘’“”…๑๒๓๔๕๖๗๘๙๐','utf-8'))})
        
        #Lemmatization
        if t in lemma_dict:
            filteredtext.append(unicode(lemma_dict[t],'utf-8'))
            
        # remove stop word
        if t not in stopwords and t.strip():
            filteredtext.append(t)

    # mark short paragraph
    if len(filteredtext) < 30:
        # print "too short paragraph => %d word" % len(filteredtext)
        short_parageaph.append(False)
    else:
        short_parageaph.append(True)

    # we will do word segmentation using only a space.            
    filteredtext = ' '.join([l for l in filteredtext])
    final_text.append(filteredtext)

# for text in final_text:
#     print text

X_count = count_vec.transform(final_text)
X_tfidf = TfidfTransformer().fit_transform(X_count)
result = clf.predict(X_tfidf)

for i in range(0,len(result)):
    if not short_parageaph[i]:
        result[i] = "0"

print """[%s]""" % ",".join('"%s"' % s for s in result)
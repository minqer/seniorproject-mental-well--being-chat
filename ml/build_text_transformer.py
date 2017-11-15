from sklearn.feature_extraction.text import CountVectorizer
from preprocess import Preprocessor
from sklearn.externals import joblib

def custom_preprocessor(str):
    # Do not perform any preprocessing here.
	return str
	
def custom_tokenizer(str):
    # Text must be segmented and separated each word by a space.
	return str.split(' ')

# intialize transformers    
count_vect = CountVectorizer(analyzer = 'word',tokenizer=custom_tokenizer,preprocessor=custom_preprocessor)

# load all text
prep = Preprocessor()
prep.load(0)

# fit transformers
print "[Transformer]: transform all text to global CountVectorizer"
texts = prep.get_all_text()
count_vect.fit_transform([text[1] for text in texts])

# export transformer
joblib.dump(count_vect, "core_model/count_vectorizer.model")
print "[Transformer]: saved"
# -*- encoding: utf-8 -*-

import codecs
import operator
import random
import string
import sys

import numpy as np
# from dummy_read_training_data import DummyN
# from impala_db import ImpalaDB
# from hive_db import HiveDB
# from read_training_data import N
from pgdb_data import DB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from word_segmentation_lexto import Tws


class Preprocessor(object):
    def __init__(self):
        #self.read = N()
        #self.read = DummyN()
        #self.read = ImpalaDB()
        # self.read = HiveDB()
        self.read = DB()
        self.tws = Tws()
        self.train_text_ratio = 0.8
        self.tag_table = {'OTHER':'0'}
        self.tag_inverse_table = {'0':'OTHER'}
        self.raw_paragraph_text = []
        self.raw_paragraph_tag = []
        self.is_inited = False
        self.test_text_id = False
        self.test_text_result = False

        # read stop words list
        self.stopwords = codecs.open('dicts/stop_words.txt', 'r','utf-8').read().split()

        # for stopword in self.stopwords:
        #     print stopword.encode('utf-8'),
        # print
        print "[Preprocess] all stopword = %d words" % len(self.stopwords)

        # read lemma dict
        lemma_dict = dict()
        with open('dicts/lemma_dict','r') as f:
            for line in f:
                lemma,words = line.split(":")
                for word in words.split(","):
                    word = word.strip()
                    lemma_dict[unicode(word,'utf-8')] = lemma

                    # print "%s => %s" % (word,lemma)
        
        self.lemma_dict = lemma_dict
        print "[Preprocess] all lemma = %d rows" % len(lemma_dict)
        
    def load(self,sample_n=0,is_verbose=False):
        # 1. word segmentation
        # 2. remove punctuation
        # 3. remove stop words
        # 4. convert tag to ID
        # 5. create doc-tag(s) style

        text = []
        tag = []

        # read raw data
        text_id,text,tag = self.read.read_text_tag()
        
        if sample_n > 0:
            text_id = text_id[:sample_n]
            text = text[:sample_n]
            tag = tag[:sample_n]
            
        print "[Preprocess]: fetch from %d paragraphs" % len(tag)

        # create 1 tag per doc raw data
        new_text = []
        new_tag = []
        
        lemma_count = 0
        stopword_count = 0

        print "[Preprocess]: preprocess..."
        for i in range(0,len(text)):
            if not text[i]:
                continue
                
            filteredtext = []
            tmp_text = self.tws.word_segment(unicode(text[i].strip(),'utf-8'))

            # preprocess
            for t in tmp_text:
                t = t.strip()
                
                # remove punctuation
                t = t.translate({ord(char): None for char in (string.punctuation + unicode('‘’“”…๑๒๓๔๕๖๗๘๙๐','utf-8'))})
                
                #Lemmatization
                if t in self.lemma_dict:
                    lemma_count += 1
                    filteredtext.append(unicode(self.lemma_dict[t],'utf-8'))
                    if is_verbose:
                        print "change %s => %s" % (t.encode('utf-8'),self.lemma_dict[t])
                  
                # remove stop word
                if t not in self.stopwords and t.strip():
                    filteredtext.append(t)
                else:
                    stopword_count += 1
                    if is_verbose:
                        print "remove '%s'" % (t)
            
            # we will do word segmentation using only a space.            
            filteredtext = ' '.join([l for l in filteredtext])
            
            tmp_tag = tag[i].split(',')
            tmp_tag = [t.strip() for t in tmp_tag]
            
            all_tag = []
            for t in tmp_tag:
                if t == '':
                    continue;
                
                all_tag.append(t)
            
            self.raw_paragraph_text.append((text_id[i],filteredtext)) #text
            self.raw_paragraph_tag.append(all_tag) #tag ID
        
        print
        print "[Preprocess]: remove punctuation %s" % (string.punctuation + '‘’“”…๑๒๓๔๕๖๗๘๙๐')
        print "[Preprocess]: apply lemma = %d pairs" % lemma_count
        print "[Preprocess]: remove stopword = %d words" % stopword_count
        
        # random sample order
        text = []
        tag = []
        m = len(self.raw_paragraph_tag)
        rand_index = random.sample(range(m),m)
        for idx in rand_index:
            text.append(self.raw_paragraph_text[idx])
            tag.append(self.raw_paragraph_tag[idx])
                        
        self.raw_paragraph_text = text
        self.raw_paragraph_tag = tag
    
        # save and index every tag
        for tag in self.read.get_all_tag():
            self.tag_table[unicode(tag[1],'utf-8')] = tag[0];
            self.tag_inverse_table[tag[0]] = unicode(tag[1],'utf-8');
        
        self.is_inited = True;
    def get_all_text(self):
        return self.raw_paragraph_text
    
    def get_train_test_data_tag(self,tag_idx,is_verbose=False):
        # 1. create 2 classes match and not match
        # 2. make classes balance (randomly select same number of sample from 2 classes)
        # 3. select train/test sample data count
        # 4. assignment a tag to each doc, tag ID (non-zero) and zero
        # 5. Zipf’s rule

        #print "Get tag %s(%d) = %d" % (self.tag_inverse_table[tag_idx],tag_idx,[tag_idx in b for b in self.raw_paragraph_tag].count(True))
        match_text = []
        not_match_text = []
        
        # separate in to 2 classes
        for idx in range(0,len(self.raw_paragraph_tag)):
            if tag_idx in self.raw_paragraph_tag[idx]:
                match_text.append(self.raw_paragraph_text[idx])
            else:
                not_match_text.append(self.raw_paragraph_text[idx])

        # select equal number of class
        if len(not_match_text) == len(match_text):
            pass
        if len(not_match_text) > len(match_text):
            random.shuffle(not_match_text)
            not_match_text = not_match_text[0:len(match_text)]
        else:
            random.shuffle(match_text)
            match_text = match_text[0:len(not_match_text)]
        
        # train/test sample count
        train_data_count = int(len(match_text)*self.train_text_ratio)
        
        test_match_text = match_text[train_data_count:]
        test_not_match_text = not_match_text[train_data_count:]
        
        train_match_text = match_text[:train_data_count]
        train_not_match_text = not_match_text[:train_data_count]
        
        # random test sample
        all_text = test_match_text + test_not_match_text
        all_tag = [tag_idx for i in range(len(test_match_text))] + [0 for i in range(len(test_not_match_text))]
        
        result_tag = []
        result_text = []
        rand_index = random.sample(range(len(all_tag)),len(all_tag))
        
        for idx in rand_index:
            result_text.append(all_text[idx])
            result_tag.append(all_tag[idx])
        
        test_text = result_text
        test_tag = result_tag
        
        # random train sample
        all_text = train_match_text + train_not_match_text
        all_tag = [tag_idx for i in range(0,len(train_match_text))] + [0 for i in range(0,len(train_not_match_text))]
        
        result_tag = []
        result_text = []
        rand_index = random.sample(range(len(all_tag)),len(all_tag))
        
        for idx in rand_index:
            result_text.append(all_text[idx])
            result_tag.append(all_tag[idx])
        
        train_text = result_text
        train_tag = result_tag
    
        # Zipf’s rule
        from collections import defaultdict
        frequency = defaultdict(int) # default = 0

        for text in train_text:
            words = text[1].split(' ')
            for token in words:
                frequency[token] += 1
        
        #FIXME
        all_word_count = len(frequency.keys())
        all_word_occur_count = sum(frequency.values())
        min_threshold = int(0.005*all_word_count)
        max_threshold = int(0.6*all_word_count)
        sorted_frequency = sorted(frequency.items(), key=operator.itemgetter(1), reverse=True)
        
        # print "*** zipf's rule ***"
        if is_verbose:
            for fword,fvalue in sorted_frequency[:20] + sorted_frequency[-20:]:
                print fword,fvalue
        
        all_filtered_word_occur_count = 0
        for i in range(len(train_text)):
            words = train_text[i][1].split(' ')
            tmp = [word for word in words if frequency[word] <= max_threshold and frequency[word] >= min_threshold]
            all_filtered_word_occur_count += len(tmp)
            train_text[i] = (train_text[i][0]," ".join(tmp)) 

        print "min=%d max=%d before=%d/%d after=%d" % (min_threshold,max_threshold,all_word_occur_count,all_word_count,all_filtered_word_occur_count)
        
        return train_text,train_tag,test_text,test_tag
        
    def get_target_names(self):
        if self.is_inited:
            return self.tag_inverse_table
        else:
            print "call load() first!"
            return False
        
    def show_tag_summary(self):
        summary = []
        for name, idx in self.tag_table.iteritems():
            summary.append(("%s(%s)" % (name,idx),[idx in t for t in self.raw_paragraph_tag].count(True)))
            
        sorted_summary= sorted(summary, key=operator.itemgetter(1), reverse=True)
        for tag, count in sorted_summary:
            print "%5d %s" % (count,tag)
    
    def get_all_tag_idx(self):
        ret = []
        if self.is_inited:
            for tag in self.tag_inverse_table.iterkeys():
                ret.append(tag)
        else:
            for tag in self.read.get_all_tag():
                ret.append(tag[0])
                
        return ret
    
    def load_test_text(self):
        text_id, text = self.read.read_test_text()
        text_result = [];
        
        lemma_count = 0
        stopword_count = 0
        
        print "[[Preprocess]: process %d text" % len(text)
        for i in range(0,len(text)):
            filteredtext = []
            tmp_text = self.tws.word_segment(unicode(text[i].strip(),'utf-8'))

            # use dummy input which has already been segmented separate by ';' 
            #tmp_text = text[i].split(';')

            # preprocess
            for t in tmp_text:
                t = t.strip()
                
                # remove punctuation
                t = t.translate({ord(char): None for char in (string.punctuation + unicode('‘’“”…๑๒๓๔๕๖๗๘๙๐','utf-8'))})
                
                #Lemmatization
                if t in self.lemma_dict:
                    lemma_count += 1
                    filteredtext.append(unicode(self.lemma_dict[t],'utf-8'))
                  
                # remove stop word
                if t not in self.stopwords and t.strip():
                    filteredtext.append(t)
                else:
                    stopword_count += 1
            
            # we will do word segmentation using only a space.            
            filteredtext = ' '.join([l for l in filteredtext])
            text_result.append(filteredtext)
        
        self.test_text_id = text_id
        self.test_text_result = text_result
    
    def get_test_text(self):
        if not self.test_text_id:
            self.load_test_text()
            
        return self.test_text_id, self.test_text_result
        
if __name__ == '__main__':              
    prep = Preprocessor()
    prep.load(0 if len(sys.argv) < 2 else int(sys.argv[1]),True)
    prep.show_tag_summary()
    
    target_tag = '44-3'
    text,tag,test_text,test_tag = prep.get_train_test_data_tag(target_tag,True)
    print "train = %d, test = %d" % (len(tag),len(test_tag))
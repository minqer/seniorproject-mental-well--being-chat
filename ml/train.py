# -*- encoding: utf-8 -*-

import os.path
import string
import sys
from collections import defaultdict
from sys import argv

import numpy as np
from preprocess import Preprocessor
from pgdb_data import DB
from sklearn import metrics
from sklearn.ensemble import (AdaBoostClassifier, BaggingClassifier,
                              GradientBoostingClassifier,
                              RandomForestClassifier, VotingClassifier)
from sklearn.externals import joblib
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import (PassiveAggressiveClassifier, Perceptron,
                                  RidgeClassifier, SGDClassifier)
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier, NearestCentroid
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from copy import deepcopy

# load CountVectorizer from file
def custom_preprocessor(str):
    # Do not perform any preprocessing here.
    return str

def custom_tokenizer(str):
    # Text must be segmented and separated each word by a space.
    return str.split(' ')

class model_trainer:

    def __init__(self):
        # read model/transformer from file
        self.model_file_dir = "core_model"
        self.count_vect_file_name = "core_model/count_vectorizer.model"

        if not os.path.isfile(self.count_vect_file_name):
            print "Build transformer first! (python build_text_transformer.py)"
            sys.exit()

        self.count_vect = joblib.load(self.count_vect_file_name)
        self.prep = Preprocessor()

        self.model_major = [
            ('SVM',  BaggingClassifier(SGDClassifier(loss='hinge', penalty='l2',alpha=1e-3, n_iter=5, random_state=42),max_samples=0.5, max_features=0.5)),
            ('NB',  BaggingClassifier(MultinomialNB(alpha=.01),max_samples=0.5, max_features=0.5)),
            # ('ANN' ,  BaggingClassifier(MLPClassifier(solver='lbfgs', alpha=1e-5,hidden_layer_sizes=(5, 2), random_state=1),max_samples=0.5, max_features=0.5)),
            # ('KNN' ,  BaggingClassifier(KNeighborsClassifier(n_neighbors=10),max_samples=0.5, max_features=0.5)),
            ('RDFOREST' , RandomForestClassifier(n_estimators=25)),
            ('NC' ,  BaggingClassifier(NearestCentroid(),max_samples=0.5, max_features=0.5)),
            ('ADA-SAMME.R', AdaBoostClassifier(n_estimators=100)),
        ]

        self.models = {
            'SVM': SGDClassifier(loss='hinge', penalty='l2',alpha=1e-3, n_iter=5, random_state=42),
            'NB': MultinomialNB(alpha=.01),
            # 'ANN' : MLPClassifier(solver='lbfgs', alpha=1e-5,hidden_layer_sizes=(5, 2), random_state=1),
            # 'KNN' : KNeighborsClassifier(n_neighbors=10),
            'RDFOREST' : RandomForestClassifier(n_estimators=25),
            'NC' : NearestCentroid(),
            # 'MAJOR' : VotingClassifier(estimators=self.model_major,voting='soft',n_jobs=-1)
        }

    def load_data(self,size=0):
        self.prep.load(size)

    def train(self,X,y,count_vect,clf,partial=False):
        X_count = count_vect.transform(X)
        X_tfidf = TfidfTransformer().fit_transform(X_count)
        
        if partial:
            clf.partial_fit(X_tfidf, y)
        else:
            clf.fit(X_tfidf, y)

    def predict(self,X,count_vect,clf):
        X_count = count_vect.transform(X)
        X_tfidf = TfidfTransformer().fit_transform(X_count)
        return clf.predict(X_tfidf)
    
    def train_all_tag(self):
        train_tag_list = []
        heightest_score = defaultdict(float)
        heightest_info = {}
        heightest_model = {}
        all_tag_idx = self.prep.get_all_tag_idx()

        for target_tag in all_tag_idx:
            for model_name in self.models:
                X_train, y_train, X_test, y_test = self.prep.get_train_test_data_tag(target_tag)

                if len(y_train) < 200:
                    print "[Train] not enough (%3d less than 100) sample for '%s'" % (
                    len(y_train), self.prep.get_target_names()[target_tag].encode('utf-8'))
                    continue

                # use only content from (paragraph_id,content)
                X_train = [data[1] for data in X_train]
                X_test = [data[1] for data in X_test]
                
                train_tag_list.append(target_tag)
                print "train %s" % target_tag
                self.train(X_train,y_train,self.count_vect,self.models[model_name],False)
                    
                predicted = self.predict(X_test,self.count_vect,self.models[model_name])
                score = np.mean(predicted == y_test)
                
                matrix = metrics.precision_recall_fscore_support(y_test, predicted,average='binary',pos_label=target_tag)
                precision = matrix[0]
                recall = matrix[1]
                f1 = matrix[2]
                
                print "%s score %.2f (%s)-[%d/%d]" % (model_name,score,self.prep.get_target_names()[target_tag].encode('utf-8'),len(y_train),len(y_test))
                print "precision=%.2f, recall=%.2f, *** f1=%.2f ***" % (precision,recall,f1)
                print

                if heightest_score[target_tag] < f1:
                    heightest_score[target_tag] = f1
                    heightest_info[target_tag] = (f1,precision,recall,score,model_name)
                    heightest_model[target_tag] = deepcopy(self.models[model_name])
        
        db = DB()
        db.clear_model_score()
        for tag in set(train_tag_list):
            if not tag in heightest_info:
                continue

            output_filename = os.path.join(self.model_file_dir,"%s.model" % tag)
            print "[Train] save model '%s' (%s) with F1=%.2f, precision=%.2f, recall=%.2f, score=%.2f : %s" % (output_filename,self.prep.get_target_names()[tag].encode('utf-8'),heightest_info[tag][0],heightest_info[tag][1],heightest_info[tag][2],heightest_info[tag][3],heightest_info[tag][4])
            joblib.dump(heightest_model[tag], output_filename)
            db.add_model_info(tag,output_filename,heightest_score[tag])
        
        return heightest_info


def train_avg(my_model,n_round=10):
    avg_acc = defaultdict(float)
    avg_f1 = defaultdict(float)
    avg_pre = defaultdict(float)
    avg_rec = defaultdict(float)

    n = n_round
    for i in range(0,n):
        info = my_model.train_all_tag()

        for tag in info:
            avg_acc[tag] += info[tag][3]
            avg_f1[tag] += info[tag][0]
            avg_pre[tag] += info[tag][1]
            avg_rec[tag] += info[tag][2]

    for key in avg_acc:
        print key, avg_acc[key]/n

    for key in avg_f1:
        print key, avg_f1[key]/n

    for key in avg_pre:
        print key, avg_pre[key]/n

    for key in avg_rec:
        print key, avg_rec[key]/n


if __name__ == "__main__":
    # if len(argv) < 3 or argv[2] not in ('new','old'):
    #     print "Usage: train <model name> <new/old>"
    #     sys.exit()

    my_model = model_trainer()
    my_model.load_data()

    info = my_model.train_all_tag()

    # train_avg(my_model,50)
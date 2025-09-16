import os
import numpy as np
import pandas as pd
import random
import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Subtract, Lambda, Concatenate, Dense
from tensorflow.keras.optimizers import Adam
from sentence_transformers import SentenceTransformer, util
import warnings
import sqlite3

warnings.filterwarnings('ignore')

items = []
labels = []
title = []
getT = True

if getT:
    try:
        connection = sqlite3.connect('db.sqlite3')  
        cursor = connection.cursor()
        query = 'SELECT title, color, category, gender FROM recomsys_item'
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            if all(len(e) > 0 for e in row):
                title.append(row[0] + " " + row[-1])
                items.append(list(row))
        cat = set()
        col = set()
        gen = set()
        for _, x, y, z in items:
            col.add(x)
            cat.add(y)
            gen.add(z)
        catd = {t: i for i, t in enumerate(cat)}
        cold = {t: i for i, t in enumerate(col)}
        gend = {t: i for i, t in enumerate(gen)}
        for _, x, y, z in items:
            labels.append([cold[x], catd[y], gend[z]])
        labels = np.array(labels)
    except Exception as e:
        print("Error while connecting to SQLite", e)
    finally:
        if connection:
            cursor.close()
            connection.close()


model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

dfname = "DataF3.pkl"

def generate_dataset():
    global title, items, dfname

    data = {'text1': [], 'text2': [], 'similarity_score': []}
    random.shuffle(title)

    for i in range(len(title)):
        for j in range(i, len(title)):
            g1 = items[i][-1].lower()
            g2 = items[j][-1].lower()

            sentence1 = title[i].lower()
            sentence2 = title[j].lower()

            weight_male = 1
            weight_female = 0.5
            weight_kid = 0.1

            weight1 = (
                weight_female if "women" in g1 else
                weight_male if "men" in g1 else
                weight_kid if "kid" in g1 else
                1.0
            )
            weight2 = (
                weight_female if "women" in g2 else
                weight_male if "men" in g2 else
                weight_kid if "kid" in g2 else
                1.0
            )

            embedding1 = model.encode(sentence1, convert_to_tensor=True)
            embedding2 = model.encode(sentence2, convert_to_tensor=True)

            weighted_embedding1 = embedding1 * weight1
            weighted_embedding2 = embedding2 * weight2

            cosine_score = util.pytorch_cos_sim(weighted_embedding1, weighted_embedding2)

            data['text1'].append(sentence1)
            data['text2'].append(sentence2)
            data['similarity_score'].append(round(cosine_score.item(), 3))
            

    df = pd.DataFrame(data)
    df.to_pickle(dfname)
    return df


embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")

def get_embeddings(sentences):
    return embed(sentences)

def newembed(df):
    if not isinstance(df, list):
        g = df.tolist()
    else:
        g = df

    final = []
    weight_male = 1
    weight_female = 0.5
    weight_kid = 0.1

    for senten in g:
        g1 = senten.split(" ")[-1]

        weight1 = (
            weight_female if "women" in g1 else
            weight_male if "men" in g1 else
            weight_kid if "kid" in g1 else
            1.0
        )

        embedding1 = model.encode(senten, convert_to_tensor=True)
        weighted_embedding1 = embedding1 * weight1
        final.append(weighted_embedding1.numpy())

    return final


model_name = "./recom4.h5"

from tensorflow.keras.layers import Layer
import keras
@keras.saving.register_keras_serializable(package="CustomLayers")
class AbsLayer(Layer):
    def call(self, inputs):
        return tf.abs(inputs)

def model_training():
    global dfname, model_name

    df = pd.read_pickle(dfname)
    df = df.sample(frac=1).reset_index(drop=True)
    new = True
    sh = 384 if new else 512

    embeddings1 = tf.convert_to_tensor(newembed(df['text1'])) if new else get_embeddings(df['text1'].tolist())
    embeddings2 = tf.convert_to_tensor(newembed(df['text2'])) if new else get_embeddings(df['text2'].tolist())

    input_1 = Input(shape=(sh,), dtype='float32')
    input_2 = Input(shape=(sh,), dtype='float32')

    diff = Subtract()([input_1, input_2])
    abs_diff = AbsLayer()(diff)
    concatenated = Concatenate()([diff, abs_diff])

    dense1 = Dense(256, activation='relu')(concatenated)
    dense2 = Dense(128, activation='relu')(dense1)
    output = Dense(1, activation='sigmoid')(dense2)

    model = Model(inputs=[input_1, input_2], outputs=output)
    model.compile(optimizer=Adam(0.0001), loss='mean_squared_error', metrics=['mae'])

    X_train = [embeddings1, embeddings2]
    y_train = df['similarity_score'].values

    model.fit(X_train, y_train, epochs=50, validation_split=0.2)
    model.save(model_name)
    print("model trained successfully")


def predict():
    global model_name
    try:
        loaded_model = tf.keras.models.load_model(model_name,safe_mode=False)
    except Exception as e:
        print(e)
        loaded_model = None
    print(loaded_model)
    sentence1 = "Blue jeans women".lower()
    sentence2 = "Blue jeans kid".lower()

    embedding1 = tf.convert_to_tensor(newembed([sentence1]))[0].numpy()
    embedding2 = tf.convert_to_tensor(newembed([sentence2]))[0].numpy()

    embedding1 = np.reshape(embedding1, (1, -1))
    embedding2 = np.reshape(embedding2, (1, -1))
    
    if loaded_model is None:
        return {"error": "Model is not trained."}
    
    similarity = loaded_model.predict([embedding1, embedding2])[0][0]
    similarity = round(float(similarity), 2)

    print("similarity",similarity)
#model_training()
#predict()

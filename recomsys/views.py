from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from .models import Item, Favlist, Wishlist, Recommend
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json, io
from django.contrib.auth.models import User
from itertools import chain
from sentence_transformers import SentenceTransformer, util
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import os
import warnings
import random

warnings.filterwarnings('ignore')

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def get_embeddings(sentences):
    return embed(sentences)

def replace_gender(sentence):
    words = sentence.lower().split()
    for i in range(len(words)):
        if words[i] in ['male', 'men', 'boy', 'man']:
            words[i] = 'men'
        elif words[i] in ['female', 'women', 'girl', 'woman', 'lady']:
            words[i] = 'women'
        elif words[i] in ['little boy', 'little girl', 'kid', 'child', 'baby']:
            words[i] = 'kid'
    return ' '.join(words)

model_name = "pretrained/recom3.h5"

def predict(query):
    global model_name
    try:
        current_path = os.path.abspath(__file__)
        model_path = os.path.join(os.path.dirname(current_path), model_name)
        loaded_model = tf.keras.models.load_model(model_path)
    except Exception:
        loaded_model = None

    sentence2 = query.lower()
    gendered_query = replace_gender(sentence2)
    if "women" in gendered_query:
        ok = Item.objects.filter(gender="Women").all()
    elif "men" in gendered_query:
        ok = Item.objects.filter(gender="Men").all()
    elif "kid" in gendered_query:
        ok = Item.objects.filter(gender="Kid").all()
    else:
        ok = Item.objects.all()

    final = []
    for i in ok:
        sentence1 = i.title.lower()
        embedding1 = get_embeddings([sentence1])[0].numpy()
        embedding2 = get_embeddings([sentence2])[0].numpy()
        embedding1 = np.reshape(embedding1, (1, -1))
        embedding2 = np.reshape(embedding2, (1, -1))
        if loaded_model is None:
            return [1, 2]
        similarity = loaded_model.predict([embedding1, embedding2])[0][0]
        similarity = round(float(similarity), 2)
        final.append([similarity, i.item_no])
    final = sorted(final, key=lambda x: x[0], reverse=True)[:10]
    return final


def weightchoice(choices, weights, num_choices):
    chosen_numbers = []
    for _ in range(num_choices):
        chosen_list = random.choices(choices, weights=weights[:len(choices)])[0]
        available_numbers = list(set(chosen_list) - set(chosen_numbers))
        if not available_numbers:
            chosen_numbers = []
        chosen_number = random.choice(available_numbers)
        chosen_numbers.append(chosen_number)
    return chosen_numbers

w = [10, 5, 1]
num = 8

def home(request):
    global w, num
    favcnt = wishcnt = 0
    recom_items = []
    if request.user.is_authenticated:
        favcnt = Favlist.objects.count()
        wishcnt = Wishlist.objects.count()
        recom = Recommend.objects.filter(user=request.user).order_by('-search_no')[:3]
        lists = [r.array for r in recom]
        choice = weightchoice(lists, w, num) if lists else []
        recom_items = Item.objects.filter(item_no__in=choice)
    return render(request, "index.html", {"favcnt": favcnt, "wishcnt": wishcnt, "recom": recom_items})

@csrf_exempt
def search(request):
    favcnt = wishcnt = 0
    prod_list = []
    if request.user.is_authenticated:
        favcnt = Favlist.objects.count()
        wishcnt = Wishlist.objects.count()
    ok = Item.objects.all()
    prod_list = ok
    if request.method == "POST":
        query = request.POST.get("query", "")
        query = replace_gender(query)
        recom_data = [j for i, j in predict(query)]
        if request.user.is_authenticated and recom_data:
            user = User.objects.get(username=request.user)
            latest_search_no = Recommend.objects.filter(user=user).order_by('-search_no').first()
            new_search_no = latest_search_no.search_no + 1 if latest_search_no else 1
            Recommend.objects.create(user=user, search_no=new_search_no, array=recom_data)
        final = []
        for i in prod_list:
            sentence1 = i.title
            sentence2 = query
            embedding1 = model.encode(sentence1, convert_to_tensor=True)
            embedding2 = model.encode(sentence2, convert_to_tensor=True)
            cosine_score = util.pytorch_cos_sim(embedding1, embedding2)
            final.append([cosine_score.item(), i])
        final = sorted(final, key=lambda x: x[0], reverse=True)[:10]
        final = [i for j, i in final]
    return render(request, "search.html", {"itm": final, "favcnt": favcnt, "wishcnt": wishcnt})

def shop(request, type, category=None):
    favcnt = wishcnt = 0
    if request.user.is_authenticated:
        favcnt = Favlist.objects.count()
        wishcnt = Wishlist.objects.count()
    if category:
        itm = Item.objects.filter(gender=type.capitalize(), category=category)
    else:
        itm = Item.objects.filter(gender=type.capitalize())
    _pageNum = request.GET.get('page')
    paginator = Paginator(itm, 10)
    try:
        pd = paginator.page(_pageNum)
    except:
        pd = paginator.page(1)
    uniquew = Item.objects.filter(gender='Women').values('category').distinct()
    categoryw = [["women", item['category']] for item in uniquew]
    uniquem = Item.objects.filter(gender='Men').values('category').distinct()
    categorym = [["men", item['category']] for item in uniquem]
    uniquek = Item.objects.filter(gender='Kid').values('category').distinct()
    categoryk = [["kid", item['category']] for item in uniquek]
    return render(request, 'shop.html', {
        'prod': pd,
        'itm': pd,
        'num': len(pd),
        'cata': type,
        'favcnt': favcnt,
        'wishcnt': wishcnt,
        'womencat': categoryw,
        'mencat': categorym,
        'kidcat': categoryk
    })

@csrf_exempt
def fav(request):
    if request.method == "POST":
        b = io.BytesIO(request.body)
        s = json.loads(b.read())
        Favlist.objects.create(
            user=User.objects.filter(pk=s['user']).first(),
            item=Item.objects.filter(item_no=s['id']).first()
        ).save()
    favcnt = wishcnt = 0
    prod_list = []
    if request.user.is_authenticated:
        favcnt = Favlist.objects.count()
        wishcnt = Wishlist.objects.count()
        ok = Favlist.objects.filter(user_id=int(request.user.id)).all()
        gg = [o.item.item_no for o in ok]
        prod_list = list(chain.from_iterable([Item.objects.filter(item_no__in=gg)]))
    return render(request, "fav.html", {"itm": prod_list, "favcnt": favcnt, "wishcnt": wishcnt})

@csrf_exempt
def wish(request):
    if request.method == "POST":
        b = io.BytesIO(request.body)
        s = json.loads(b.read())
        Wishlist.objects.create(
            user=User.objects.filter(pk=s['user']).first(),
            item=Item.objects.filter(item_no=s['id']).first()
        ).save()
    favcnt = wishcnt = 0
    prod_list = []
    if request.user.is_authenticated:
        favcnt = Favlist.objects.count()
        wishcnt = Wishlist.objects.count()
        ok = Wishlist.objects.filter(user_id=int(request.user.id)).all()
        gg = [o.item.item_no for o in ok]
        prod_list = list(chain.from_iterable([Item.objects.filter(item_no__in=gg)]))
    return render(request, "shop-cart.html", {"favcnt": favcnt, "wishcnt": wishcnt, 'item': prod_list})

def checkout(request):
    favcnt = wishcnt = 0
    if request.user.is_authenticated:
        favcnt = Favlist.objects.count()
        wishcnt = Wishlist.objects.count()
    return render(request, "shop-cart.html", {"favcnt": favcnt, "wishcnt": wishcnt})

def details(request, id):
    favcnt = wishcnt = 0
    if request.user.is_authenticated:
        favcnt = Favlist.objects.count()
        wishcnt = Wishlist.objects.count()
    item = Item.objects.filter(pk=id).first()
    return render(request, "product-details.html", {"itm": item, "favcnt": favcnt, "wishcnt": wishcnt})

@csrf_exempt
def delete(request):
    if request.method == "POST":
        b = io.BytesIO(request.body)
        s = json.loads(b.read())
        if s['l'] == 1:
            try:
                item = get_object_or_404(Favlist, user__id=s['user'], item__item_no=s['id'])
                item.delete()
            except Http404:
                pass
            return HttpResponse("successful")
        if s['l'] == 2:
            try:
                item = get_object_or_404(Wishlist, user__id=s['user'], item__item_no=s['id'])
                item.delete()
            except Http404:
                pass
            return HttpResponse("successful")

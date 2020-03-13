import numpy as np
import pandas as pd
from flask import Flask, request, Response, render_template
from sklearn.metrics.pairwise import sigmoid_kernel
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import pairwise_distances
from fuzzywuzzy import fuzz
from IPython.display import HTML



products = pd.read_csv('./data/products_combined.csv')


#CountVactorizer splits the ingredients by comma and not in to individual words
cvec = CountVectorizer(tokenizer=lambda x: x.split(', '))
#training CountVectorizer and transforming
cvec_words = cvec.fit_transform(products['ingredients'])
#calculating the pairwise distance for products
recommender = pairwise_distances(cvec_words, metric='cosine')

#building a recommender DataFrame
recommender_df = pd.DataFrame(recommender, columns=products['name'], index=products['name'])


#starting the Flask
app = Flask('__name__')

@app.route('/')
@app.route('/form')

def form():
    return render_template('page1.html')

@app.route('/submit')

def submit():
    user_input = request.args.get('sephoraproduct')
    #making sure user input is going to be interpreted properly
    titles = products[products['name'].str.lower().str.contains(user_input.lower())]
    titles.reset_index(inplace = True)
    titles= titles.drop(columns = ['index'])
    try:
        searched_item = titles.iloc[0,0]
        searched_category = products[products['name'] == searched_item]['category'].values[0]
        searched_brand = products[products['name'] == searched_item]['brand'].values[0]
        #if the product is already part of 'clean sephora'
        if products[(products['name'] == searched_item) & (products['store'] == 'Sephora')]['type'].values == 'clean':
            brand_other = products[(products['brand'] == searched_brand) & (products['store'] == 'Sephora')]
            brand_other = brand_other[brand_other['name'] != searched_item]
            print_to_screen = brand_other.sample(n=5)
            print_to_screen = print_to_screen[['name', 'brand', 'price', 'store', 'website']]
            return render_template('page4.html', searched_item = searched_item, searched_brand = searched_brand,
                                    tables=[HTML(print_to_screen.to_html(classes='data', header = True, index = False,escape = False))])
        #if the product is not part of clean sephora
        else:

            df = pd.DataFrame(recommender_df[searched_item].index)
            df['score'] = recommender_df[searched_item].values
            df[['brand', 'category', 'price', 'store', 'url', 'type', 'website']] = products[['brand',
                                                                                   'category', 'price', 'store', 'url', 'type', 'website']]
            #pulling out only the same category of the searched item
            appropriete_category = df[(df['category'] == searched_category) &(df['type'] == 'clean')].sort_values(by = 'score')
            #first table is the clean sephora recommentations
            clean_sephora_recommendation = appropriete_category[appropriete_category['store'] == 'Sephora']
            print_to_screen_sep = clean_sephora_recommendation[['name', 'brand', 'price', 'store', 'website']]
            print_to_screen_sep = print_to_screen_sep[print_to_screen_sep['name'] != searched_item]
            print_to_screen_sep = print_to_screen_sep[0:5]

            #second table is the other clean stores
            other_clean = appropriete_category[appropriete_category['store'] != 'Sephora']
            print_to_screen_other = other_clean[['name', 'brand', 'price', 'store', 'website']]
            print_to_screen_other = print_to_screen_other[print_to_screen_other['name'] != searched_item]
            print_to_screen_other = print_to_screen_other[0:5]


            return render_template('page2.html',
                                sephoraproduct = searched_item,
                                productbrand = searched_brand,
                                tables=[HTML(print_to_screen_sep.to_html(classes='data', header = True, index = False, escape = False))],
                                tables2=[HTML(print_to_screen_other.to_html(classes='data', header = True, index = False, escape = False))])
    except: #if the product is not in our database it takes it to a mistake page
        fuzzy = []
        for k in products.name:
            fuzzy.append((k, fuzz.ratio(k.lower(), user_input.lower())))
        fuzzy_ratio = pd.DataFrame(fuzzy, columns = ['name', 'ratio'])
        similar = fuzzy_ratio.sort_values(by = 'ratio', ascending = False)
        similar = similar[0:5]
        similar.reset_index(inplace=True)
        similar.drop(['index', 'ratio'], axis = 1, inplace = True)
        for index, item in enumerate(similar.name):
            similar.loc[index,'brand']=products[products['name'] == item]['brand'].values[0]
            similar.loc[index,'price'] = products[products['name'] == item]['price'].values[0]
            similar.loc[index,'store'] = products[products['name'] == item]['store'].values[0]
            similar.loc[index,'website'] = products[products['name'] == item]['website'].values[0]
        return render_template('page3.html',
                                giberish = user_input,
                                tables=[HTML(similar.to_html(classes='data', header = True, index = False,escape = False))])



if __name__ == '__main__':
    app.run(debug = True)

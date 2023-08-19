from flask import Flask, render_template, redirect, jsonify, url_for, session
import pickle
import numpy as np
import pandas as pd

app=Flask(__name__)
app.secret_key = 'FlipkartGrid'

popular_df=pd.read_csv('popular_dataset.csv')
products = pd.read_csv('products.csv')

pt = pickle.load(open('pt.pkl','rb'))
df_main = pickle.load(open('df_main.pkl','rb'))

similarity_score = pickle.load(open('similarity_score.pkl','rb'))
cosine_similarity = pickle.load(open('cosine_similarity.pkl','rb'))

def convert_to_stars(rating):
    rating = float(rating)
    full_stars = int(rating)
    half_star = rating - full_stars >= 0.5
    return {'full_stars': full_stars, 'half_star': half_star}

@app.route('/')
def index():
    return render_template('index.html',
    product_names=list(popular_df['product_name'].values),
    img_links=list(popular_df['img_link'].values),
    ratings=list(popular_df['avg_rating'].values),
    prices=list(popular_df['discounted_price'].values),
    product_ids=list(popular_df['product_id'].values),
    convert_to_stars = convert_to_stars
)



@app.route('/Recommend')
def recommed():
    orders = session.get('orders', [])
    data1=[]
    for order in orders:
        product_name=order['item_name']
        index=np.where(pt.index==product_name)[0][0]
        similar_items=sorted(list(enumerate(similarity_score[index])),key=lambda x:x[1],reverse=True)[1:4]
        for i in similar_items:
            item=[]
            temp_df=df_main[df_main['product_name']==pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('product_name')['product_name'].values))
            item.extend(list(temp_df.drop_duplicates('product_name')['img_link'].values))
            item.extend(list(temp_df.drop_duplicates('product_name')['discounted_price'].values))
            item.extend(list(temp_df.drop_duplicates('product_name')['rating'].values))
            item.extend(list(temp_df.drop_duplicates('product_name')['product_id'].values))
            if item not in data1:
                data1.append(item)

    data2=[]
    for order in orders:
        product_name=order['item_name']
        product_index = products[products['product_name'] == product_name].index[0]
        user_scores = list(enumerate(cosine_similarity[product_index]))
        top_recommendations = sorted(user_scores, key=lambda x:x[1], reverse= True)
        top_recommendations = top_recommendations[1:3]

        for i in top_recommendations:
            item={}
            item['name'] = products.iloc[i[0]]['product_name']
            item['price'] = products.iloc[i[0]]['discounted_price']
            item['img_link'] = products.iloc[i[0]]['img_link']
            item['rating'] = products.iloc[i[0]]['rating']
            print(type(item['rating']))
            item['product_id'] = products.iloc[i[0]]['product_id']

            if item not in data2:
                data2.append(item)


    return render_template('recommend.html',products=data1,products2=data2,convert_to_stars = convert_to_stars)


@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<string:product_id>')
def add_to_cart(product_id):
    cart_items = session.get('cart', [])
    
    # Locate the product in the DataFrame using product_id
    product_series = popular_df.loc[popular_df['product_id'] == product_id].iloc[0]
    
    
    # Convert the Series to a dictionary
    product = product_series.to_dict()
   
    
    if product is not None:
        # Check if the product is already in the cart
        existing_product = next((p for p in cart_items if p['product_id'] == product_id), None)
        if existing_product:
            existing_product['quantity'] += 1
        else:
            product_copy = product.copy()
            product_copy['quantity'] = 1
            price = int(''.join(filter(str.isdigit, product['discounted_price'])))
            product_copy['price'] = price
            cart_items.append(product_copy)
            
        session['cart'] = cart_items
    return redirect(url_for('index'))

@app.route('/add_to_cart_recommend/<string:product_id>')
def add_to_cart_recommend(product_id):
    cart_items = session.get('cart', [])
    
    # Locate the product in the df_main DataFrame using product_id
    product_series = df_main.loc[df_main['product_id'] == product_id].iloc[0]
    
    
    # Convert the Series to a dictionary
    product = product_series.to_dict()
   
    
    if product is not None:
        # Check if the product is already in the cart
        existing_product = next((p for p in cart_items if p['product_id'] == product_id), None)
        if existing_product:
            existing_product['quantity'] += 1
        else:
            product_copy = product.copy()
            product_copy['quantity'] = 1
            price = int(''.join(filter(str.isdigit, product['discounted_price'])))
            product_copy['price'] = price
            cart_items.append(product_copy)
            
        session['cart'] = cart_items
    return redirect(url_for('cart'))

@app.route('/remove_item/<string:item_id>', methods=['POST'])
def remove_item(item_id):
    cart = session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != item_id]
    session['cart'] = cart
    return jsonify(success=True)

@app.route('/buy', methods=['POST'])
def buy():
    cart_items = session.get('cart', [])
    orders = session.get('orders', [])

    for item in cart_items:
        order = {
            'item_id': item['product_id'],
            'item_name': item['product_name'],
            'quantity': item['quantity'],
            'total_price': item['price'] * item['quantity'],
            'image_url': item['img_link'],
        }
        orders.append(order)
       
        

    # Clear the cart (empty the session)
    session['cart'] = []
    session['orders'] = orders

    return jsonify(orders=orders)

@app.route('/orders')
def orders():
    orders = session.get('orders', [])
    return render_template('orders.html', orders=orders)

@app.route('/logout')
def logout():
    session.clear()
    return jsonify(success=True)

if __name__== "__main__":
    app.run(debug=True)
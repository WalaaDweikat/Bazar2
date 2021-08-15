from flask import Flask, json, jsonify ,render_template
from flask import request
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
order_counter=1
catalog_counter=1

#front end tier will send requests to order server and catalog server 
cache_size =  5
id_count = {}

#initial app
app = Flask(__name__)


#Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///frontEndCache.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#init database
db = SQLAlchemy(app)

#init marshmallow
ma = Marshmallow(app)

#catalog Class/Model
class Catalog(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    topic = db.Column(db.String(200))
     

    def __init__(self,id,title,quantity,price,topic):
        self.id=id
        self.title=title
        self.quantity=quantity
        self.price=price
        self.topic=topic
      

#Catalog schema
class CatalogSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title' , 'quantity' , 'price' , 'topic')

db.create_all()
#init schema
book_schema = CatalogSchema()
books_schema = CatalogSchema(many=True)


#request to get all of the books information # it is sent to the catalog server
@app.route('/bazar/info/all', methods=['GET'])
def info():
  global catalog_counter
  if catalog_counter == 1:
    r = requests.get("http://192.168.1.202:2000/bazar/info/all")
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 2:
    r = requests.get("http://192.168.1.202:3000/bazar/info/all")  
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 3:
    r = requests.get("http://192.168.1.202:4000/bazar/info/all")  
    catalog_counter = 1
  return (r.content)

#request to catalog to get info about book with the id book_id
@app.route('/bazar/info/<int:book_id>', methods=['GET'])
def get_info(book_id):
  book_id = book_id
  #this is the request to be sent to the catalog server
  global catalog_counter
  global cache_size
  global id_count
  book = Catalog.query.with_entities(Catalog.title,Catalog.quantity,Catalog.topic,Catalog.price).filter_by(id = book_id).first()
  print("enter function and get books from db")
  if book: 
    print("if found in db")
    id_count[book_id] = id_count[book_id] + 1
    return book_schema.jsonify(book)
  else:
    print("if not found in db") 
    if catalog_counter == 1:
      r = requests.get("http://192.168.1.202:2000/bazar/info/"+str(book_id))
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 2:
      r = requests.get("http://192.168.1.202:3000/bazar/info/"+str(book_id))  
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 3:
      r = requests.get("http://192.168.1.202:4000/bazar/info/"+str(book_id))  
      catalog_counter = 1
    res = r.json()
    c = Catalog(book_id, res['title'], res['quantity'] , res['price'] , res['topic'])
    if cache_size > 0 :
      print("if there is a space for book in the cache")
      db.session.add(c)
      db.session.commit()
      id_count[book_id] = 1
      cache_size=cache_size-1      
    elif cache_size <= 0 :
      print("if there is not a space for book in the cache")
      min = 100000000
      k = -1
      for key in id_count :
        if min > id_count[key]: 
          min = id_count[key]
          k = key
          break
      del id_count[k] 
      id_count[book_id] = 1
      Catalog.query.filter_by(id=k).delete()  
      print("delete from db")
      db.session.add(c)
      db.session.commit()
    return (r.content)

#getting the books info which have the topic s_topic #request to catalogServer
@app.route('/bazar/search/<s_topic>', methods=['GET'])
def search(s_topic):
  s_topic = s_topic
  topic_1="distributed systems"
  topic_2="undergraduate school"
  topic_3="new"
  global cache_size
  global id_count
  global catalog_counter
  books = Catalog.query.with_entities(Catalog.id,Catalog.title,Catalog.quantity,Catalog.topic,Catalog.price).filter_by(topic=s_topic.replace("%20"," ")).all()
  result =jsonify(books_schema.dump(books))
  num = len(books)
  print(num)
  ################################################### topic 1
  if (books)and(s_topic==topic_1)and(num == 1):
    b = books[0]
    Catalog.query.filter_by(id=b.id).delete()  
    print("delete from db")
    db.session.commit()
    if catalog_counter == 1:
      r = requests.get("http://192.168.1.202:2000/bazar/search/"+str(s_topic))
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 2:
      r = requests.get("http://192.168.1.202:3000/bazar/search/"+str(s_topic))  
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 3:
      r = requests.get("http://192.168.1.202:4000/bazar/search/"+str(s_topic))  
      catalog_counter = 1
    res=r.json()
    book_1 = Catalog(res[0]['id'], res[0]['title'], res[0]['quantity'] , res[0]['price'] , res[0]['topic'])
    book_2 = Catalog(res[1]['id'], res[1]['title'], res[1]['quantity'] , res[1]['price'] , res[1]['topic'])
    if cache_size-2 > 0 :
      db.session.add(book_1)
      db.session.commit()
      db.session.add(book_2)
      db.session.commit()
      id_count[res[0]['id']] = 1
      id_count[res[1]['id']] = 1
      cache_size -= 2      
    elif cache_size-2 <= 0 :
      min1 = 100000000
      min2 = 100000000
      k1 = -1
      k2 = -1
      for key in id_count :
        if min1 > id_count[key]: 
          min1 = id_count[key]
          k1 = key
          del id_count[key]
          break
      for key in id_count :
        if min2 > id_count[key]: 
          min2 = id_count[key]
          k2 = key
          del id_count[key]
          break
      id_count[res[0]['id']] = 1
      id_count[res[1]['id']] = 1
      Catalog.query.filter_by(id=k1).delete()  
      print("delete from db")
      db.session.commit()
      Catalog.query.filter_by(id=k2).delete()  
      print("delete from db")
      db.session.commit()
      db.session.add(book_1)
      db.session.commit()
      db.session.add(book_2)
      db.session.commit()
    return r.content
  elif (books)and(s_topic==topic_1)and(num == 2):
    id_count[books[0].id]+=1
    id_count[books[1].id]+=1
    return result
  ################################################# topic 2
  if (books)and(s_topic==topic_2)and(num == 1):
    b = books[0]
    Catalog.query.filter_by(id=b.id).delete()  
    print("delete from db")
    db.session.commit()
    if catalog_counter == 1:
      r = requests.get("http://192.168.1.202:2000/bazar/search/"+str(s_topic))
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 2:
      r = requests.get("http://192.168.1.202:3000/bazar/search/"+str(s_topic))  
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 3:
      r = requests.get("http://192.168.1.202:4000/bazar/search/"+str(s_topic))  
      catalog_counter = 1
    res=r.json()
    book_1 = Catalog(res[0]['id'], res[0]['title'], res[0]['quantity'] , res[0]['price'] , res[0]['topic'])
    book_2 = Catalog(res[1]['id'], res[1]['title'], res[1]['quantity'] , res[1]['price'] , res[1]['topic'])
    if cache_size-2 > 0 :
      db.session.add(book_1)
      db.session.commit()
      db.session.add(book_2)
      db.session.commit()
      id_count[res[0]['id']] = 1
      id_count[res[1]['id']] = 1
      cache_size -= 2      
    elif cache_size-2 <= 0 :
      min1 = 100000000
      min2 = 100000000
      k1 = -1
      k2 = -1
      for key in id_count :
        if min1 > id_count[key]: 
          min1 = id_count[key]
          k1 = key
          del id_count[key]
          break
      for key in id_count :
        if min2 > id_count[key]: 
          min2 = id_count[key]
          k2 = key
          del id_count[key]
          break
      id_count[res[0]['id']] = 1
      id_count[res[1]['id']] = 1
      Catalog.query.filter_by(id=k1).delete()  
      print("delete from db")
      db.session.commit()
      Catalog.query.filter_by(id=k2).delete()  
      print("delete from db")
      db.session.commit()
      db.session.add(book_1)
      db.session.commit()
      db.session.add(book_2)
      db.session.commit()
    return r.content
  elif (books)and(s_topic==topic_2)and(num == 2):
    id_count[books[0].id] += 1
    id_count[books[1].id] += 1
    return result
 ################################################# topic 3
  if (books)and(s_topic==topic_3)and((num == 1)or(num==2)):
    if(num==1):
      b = books[0]
      Catalog.query.filter_by(id=b.id).delete()  
      print("delete from db")
      db.session.commit()
    elif(num==2):
      b = books[0]
      c = books[1]
      Catalog.query.filter_by(id=b.id).delete()  
      print("delete from db")
      db.session.commit()
      Catalog.query.filter_by(id=c.id).delete()  
      print("delete from db")
      db.session.commit()
    if catalog_counter == 1:
      r = requests.get("http://192.168.1.202:2000/bazar/search/"+str(s_topic))
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 2:
      r = requests.get("http://192.168.1.202:3000/bazar/search/"+str(s_topic))  
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 3:
      r = requests.get("http://192.168.1.202:4000/bazar/search/"+str(s_topic))  
      catalog_counter = 1
    res=r.json()
    book_1 = Catalog(res[0]['id'], res[0]['title'], res[0]['quantity'] , res[0]['price'] , res[0]['topic'])
    book_2 = Catalog(res[1]['id'], res[1]['title'], res[1]['quantity'] , res[1]['price'] , res[1]['topic'])
    book_3 = Catalog(res[2]['id'], res[2]['title'], res[2]['quantity'] , res[2]['price'] , res[2]['topic'])
    if cache_size-3 > 0 :
      db.session.add(book_1)
      db.session.commit()
      db.session.add(book_2)
      db.session.commit()
      db.session.add(book_3)
      db.session.commit()
      id_count[res[0]['id']] = 1
      id_count[res[1]['id']] = 1
      id_count[res[2]['id']] = 1
      cache_size -= 3      
    elif cache_size-3 <= 0 :
      min1 = 100000000
      min2 = 100000000
      min3 = 100000000
      k1 = -1
      k2 = -1
      k3 = -1
      for key in id_count :
        if min1 > id_count[key]: 
          min1 = id_count[key]
          k1 = key
          del id_count[k1]
          break
      for key in id_count :
        if min2 > id_count[key]: 
          min2 = id_count[key]
          k2 = key
          del id_count[k2]
          break
      for key in id_count :
        if min3 > id_count[key]: 
          min3 = id_count[key]
          k3 = key
          del id_count[k3]
          break
      id_count[res[0]['id']] = 1
      id_count[res[1]['id']] = 1
      id_count[res[2]['id']] = 1
      Catalog.query.filter_by(id=k1).delete()  
      print("delete from db")
      db.session.commit()
      Catalog.query.filter_by(id=k2).delete()  
      print("delete from db")
      db.session.commit()
      Catalog.query.filter_by(id=k3).delete()  
      print("delete from db")
      db.session.commit()
      db.session.add(book_1)
      db.session.commit()
      db.session.add(book_2)
      db.session.commit()
      db.session.add(book_3)
      db.session.commit()
    return r.content
  elif (books)and(s_topic==topic_3)and(num == 3):
    id_count[books[0].id]+=1
    id_count[books[1].id]+=1
    id_count[books[2].id]+=1
    return result
 ###########################################
  if not(books):
    if catalog_counter == 1:
      r = requests.get("http://192.168.1.202:2000/bazar/search/"+str(s_topic))
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 2:
      r = requests.get("http://192.168.1.202:3000/bazar/search/"+str(s_topic))  
      catalog_counter = catalog_counter + 1
    elif catalog_counter == 3:
      r = requests.get("http://192.168.1.202:4000/bazar/search/"+str(s_topic))  
      catalog_counter = 1
    res=r.json()
    num=len(res)
    if (num ==2):
      book_1 = Catalog(res[0]['id'], res[0]['title'], res[0]['quantity'] , res[0]['price'] , res[0]['topic'])
      book_2 = Catalog(res[1]['id'], res[1]['title'], res[1]['quantity'] , res[1]['price'] , res[1]['topic'])
      if cache_size-2 > 0 :
        db.session.add(book_1)
        db.session.commit()
        db.session.add(book_2)
        db.session.commit()
        id_count[res[0]['id']] = 1
        id_count[res[1]['id']] = 1
        cache_size -= 2      
      elif cache_size-2 <= 0 :
        min1 = 100000000
        min2 = 100000000
        k1 = -1
        k2 = -1
        for key in id_count :
          if min1 > id_count[key]: 
            min1 = id_count[key]
            k1 = key
            del id_count[key]
            break
        for key in id_count :
          if min2 > id_count[key]: 
            min2 = id_count[key]
            k2 = key
            del id_count[key]
            break
        Catalog.query.filter_by(id=k1).delete()
        Catalog.query.filter_by(id=k2).delete()
        id_count[res[0]['id']] = 1
        id_count[res[1]['id']] = 1
        db.session.add(book_1)
        db.session.commit()
        db.session.add(book_2)
        db.session.commit()
    elif (num==3):
      book_1 = Catalog(res[0]['id'], res[0]['title'], res[0]['quantity'] , res[0]['price'] , res[0]['topic'])
      book_2 = Catalog(res[1]['id'], res[1]['title'], res[1]['quantity'] , res[1]['price'] , res[1]['topic'])
      book_3 = Catalog(res[2]['id'], res[2]['title'], res[2]['quantity'] , res[2]['price'] , res[2]['topic'])
      if cache_size-3 > 0 :
        db.session.add(book_1)
        db.session.commit()
        db.session.add(book_2)
        db.session.commit()
        db.session.add(book_3)
        db.session.commit()
        id_count[res[0]['id']] = 1
        id_count[res[1]['id']] = 1
        id_count[res[2]['id']] = 1
        cache_size -= 3      
      elif cache_size-3 <= 0 :
        min1 = 100000000
        min2 = 100000000
        min3 = 100000000
        k1 = -1
        k2 = -1
        k3 = -1
        for key in id_count :
          if min1 > id_count[key]: 
            min1 = id_count[key]
            k1 = key
            del id_count[key]
            break
        for key in id_count :
          if min2 > id_count[key]: 
            min2 = id_count[key]
            k2 = key
            del id_count[key]
            break
        for key in id_count :
          if min3 > id_count[key]: 
            min3 = id_count[key]
            k3 = key
            del id_count[key]
            break
        Catalog.query.filter_by(id=k1).delete()
        Catalog.query.filter_by(id=k2).delete()
        Catalog.query.filter_by(id=k3).delete()
        id_count[res[0]['id']] = 1
        id_count[res[1]['id']] = 1
        id_count[res[2]['id']] = 1
        db.session.add(book_1)
        db.session.commit()
        db.session.add(book_2)
        db.session.commit()
        db.session.add(book_3)
        db.session.commit()
    print (r.content)
    return r.content

#purchase to order server, there is a parameter called amount can be send with the request body to 
#specify how many books to purchase it will 1 by default if there is no body sent with the request 
@app.route('/bazar/purchase/<int:book_id>', methods=['POST'])
def purchase(book_id):
  book_id = book_id
  if request.data:#if there is an amount sent with the request`s body 
     amount=request.json['amount']
  else :
     amount=1 #the default value is one 
  #this is the reqest to be sent to the order server
  global catalog_counter
  if catalog_counter == 1:
    #r = requests.post("http://192.168.1.203:2000/bazar/purchase/"+str(book_id),data={'amount':amount}) 
    r = requests.post("http://192.168.1.121:2000/bazar/purchase/"+str(book_id),data={'amount':amount}) 
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 2:
    #r = requests.post("http://192.168.1.203:3000/bazar/purchase/"+str(book_id),data={'amount':amount}) 
    r = requests.post("http://192.168.1.121:3000/bazar/purchase/"+str(book_id),data={'amount':amount}) 
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 3:
    #r = requests.post("http://192.168.1.203:4000/bazar/purchase/"+str(book_id),data={'amount':amount}) 
    r = requests.post("http://192.168.1.121:6000/bazar/purchase/"+str(book_id),data={'amount':amount}) 
    catalog_counter = 1
  return (r.content)

############################################################# for admin ######################################
#the following requests is sent form the admin of the book store 

#update the price of a book 
@app.route('/bazar/update_price/<int:book_id>', methods=['PUT'])
def update_book_price(book_id):
  book_id = book_id
  price = request.json['price']
  global catalog_counter
  if catalog_counter == 1:
    r = requests.put("http://192.168.1.202:2000/bazar/update_price/"+str(book_id),data={'price':price})
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 2:
    r = requests.put("http://192.168.1.202:3000/bazar/update_price/"+str(book_id),data={'price':price})
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 3:
    r = requests.put("http://192.168.1.202:4000/bazar/update_price/"+str(book_id),data={'price':price})
    catalog_counter = 1
  return (r.content)


#increase quantity 
@app.route('/bazar/increase_quantity/<int:book_id>', methods=['PUT'])
def increase_book_quantity(book_id):
  book_id = book_id
  amount = request.json['amount']
  global catalog_counter
  if catalog_counter == 1:
    r = requests.put("http://192.168.1.202:2000/bazar/increase_quantity/"+str(book_id),data={'amount':amount})
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 2:
    r = requests.put("http://192.168.1.202:3000/bazar/increase_quantity/"+str(book_id),data={'amount':amount})
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 3:
    r = requests.put("http://192.168.1.202:4000/bazar/increase_quantity/"+str(book_id),data={'amount':amount})
    catalog_counter = 1
  return (r.content)

#decrease quantity 
@app.route('/bazar/decrease_quantity/<int:book_id>', methods=['PUT'])
def decrease_book_quantity(book_id):
  book_id = book_id
  amount = request.json['amount']
  global catalog_counter
  if catalog_counter == 1:
    r = requests.put("http://192.168.1.202:2000/bazar/decrease_quantity/"+str(book_id),data={'amount':amount})
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 2:
    r = requests.put("http://192.168.1.202:3000/bazar/decrease_quantity/"+str(book_id),data={'amount':amount})
    catalog_counter = catalog_counter + 1
  elif catalog_counter == 3:
    r = requests.put("http://192.168.1.202:4000/bazar/decrease_quantity/"+str(book_id),data={'amount':amount})
    catalog_counter = 1
  return (r.content)


@app.route('/bazar/delete/<int:book_id>', methods=['DELETE'])
def delete(book_id):
  book_id = book_id
  global order_counter
  dc = Catalog.query.get(book_id)
  if dc:
    db.session.delete(dc)
    db.session.commit()
    id_count[book_id] = 0
    return jsonify({'msg':"done"})
  else:
    return jsonify({'msg':"not found"})


#to show the orders list
@app.route('/bazar/order/show', methods=['GET'])
def show():
  global order_counter
  if order_counter == 1:
    r = requests.get("http://192.168.1.121:2000/show")
    order_counter = order_counter + 1
  elif order_counter == 2:
    r = requests.get("http://192.168.1.121:3000/show")
    order_counter =  order_counter + 1
  elif  order_counter == 3:
    r = requests.get("http://192.168.1.121:6000/show")
    order_counter = 1
  return (r.content)
#catalog= 202
#order = 203
#run
if __name__=="__main__":
    app.run(debug=True)
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from .models import Customer, Product, Cart, OrderPlaced
from .forms import CustomerRegistrationForm, CustomerProfileForm
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import requests


def your_queries_view(request):
	# Set the request parameters
	username = request.user.username
	url = 'https://dev75585.service-now.com/api/now/table/incident?u_username={}'.format(username)
	user = 'admin'
	pwd = 'o!i=NkLi10PK'
	headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # Do the HTTP request
	response = requests.get(url, auth=(user, pwd), headers=headers)

    # Check for HTTP codes other than 200
	if response.status_code != 200:
		error_message = 'Error occurred. Status: {} - {}'.format(response.status_code, response.reason)
		return render(request, 'app/error.html', {'error_message': error_message})

    # Decode the JSON response into a dictionary and use the data
	data = response.json()

    # Extract required fields from each incident record
	incidents = []
	i = 0

	for incident in data['result']:
		i = i+1
		u_username = incident.get('u_username')
		number = incident.get('number')
		category = incident.get('category')
		state = incident.get('state')
		if state == '1':
			state = 'New'
			
		elif state == '2':
			state = 'In Progress'
			
		elif state == '3':
			state = 'On Hold'

		elif state == '6':
			state = 'Resolved'

		elif state == '7':
			state = 'Closed'

		else :
			state = 'Cancelled'
        

		priority = incident.get('priority')
		short_description = incident.get('short_description')
		assignment_group = incident.get('assignment_group')
		description = incident.get('description')
		u_solution = incident.get('u_solution')

        # Add the extracted fields to the incidents list
		incidents.append({
			'i':i,
			'u_username': u_username,
            'category': category,
			'state': state,
			'short_description': short_description,
			'description': description,
			'u_solution': u_solution
			})
	return render(request, 'app/your_queries.html', {'incidents': incidents})


def submit_query(request):
	success_message = None
	if request.method=='POST':
		url='https://dev75585.service-now.com/api/now/table/incident'
		usr='admin'
		pwrd='o!i=NkLi10PK'
		username = request.user.username
		#username=request.POST.get('username')
		company=request.POST.get('company')
		short_description=request.POST.get('short_description')
		description=request.POST.get('description')
		contact_type='FERTIZO'
		priority='1 - Critical'
		headers={"Content-Type": "application/json", "Accept": "application/json"}
		data={"u_username":username,"category":company,"contact_type":contact_type,"priority":priority,"short_description":short_description,"description":description}
		response = requests.post(url, auth=(usr, pwrd), headers=headers, json=data)
		#print(response)
		if response.status_code == 200 or response.status_code == 201 or response.status_code == 202 or response.status_code == 203:
			success_message = "Congratulations, your operation was successful."
						
		else:
			return render(request, 'app/error.html', {'response': response})
		
		return render(request, 'app/base.html', {'success_message': success_message})


def success_page(request):
    return render(request, 'app/success.html')


class ProductView(View):
	def get(self, request):
		totalitem = 0
		splinkers = Product.objects.filter(category='SP')
		pipes = Product.objects.filter(category='PI')
		fertilizers = Product.objects.filter(category='F')
		pesticides = Product.objects.filter(category='P')
		seeds = Product.objects.filter(category='S')
		if request.user.is_authenticated:
			totalitem = len(Cart.objects.filter(user=request.user))
		return render(request, 'app/home.html', {'splinkers':splinkers, 'pipes':pipes, 'fertilizers':fertilizers, 'pesticides':pesticides,'seeds':seeds,'totalitem':totalitem})

class ProductDetailView(View):
	def get(self, request, pk):
		totalitem = 0
		product = Product.objects.get(pk=pk)
		print(product.id)
		item_already_in_cart=False
		if request.user.is_authenticated:
			totalitem = len(Cart.objects.filter(user=request.user))
			item_already_in_cart = Cart.objects.filter(Q(product=product.id) & Q(user=request.user)).exists()
		return render(request, 'app/productdetail.html', {'product':product, 'item_already_in_cart':item_already_in_cart, 'totalitem':totalitem})

@login_required()
def add_to_cart(request):
	user = request.user
	item_already_in_cart1 = False
	product = request.GET.get('prod_id')
	item_already_in_cart1 = Cart.objects.filter(Q(product=product) & Q(user=request.user)).exists()
	if item_already_in_cart1 == False:
		product_title = Product.objects.get(id=product)
		Cart(user=user, product=product_title).save()
		messages.success(request, 'Product Added to Cart Successfully !!' )
		return redirect('/cart')
	else:
		return redirect('/cart')
  # Below Code is used to return to same page
  # return redirect(request.META['HTTP_REFERER'])

@login_required
def show_cart(request):
	totalitem = 0
	if request.user.is_authenticated:
		totalitem = len(Cart.objects.filter(user=request.user))
		user = request.user
		cart = Cart.objects.filter(user=user)
		amount = 0.0
		shipping_amount = 70.0
		totalamount=0.0
		cart_product = [p for p in Cart.objects.all() if p.user == request.user]
		print(cart_product)
		if cart_product:
			for p in cart_product:
				tempamount = (p.quantity * p.product.discounted_price)
				amount += tempamount
			totalamount = amount+shipping_amount
			return render(request, 'app/addtocart.html', {'carts':cart, 'amount':amount, 'totalamount':totalamount, 'totalitem':totalitem})
		else:
			return render(request, 'app/emptycart.html', {'totalitem':totalitem})
	else:
		return render(request, 'app/emptycart.html', {'totalitem':totalitem})

def plus_cart(request):
	if request.method == 'GET':
		prod_id = request.GET['prod_id']
		c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
		c.quantity+=1
		c.save()
		amount = 0.0
		shipping_amount= 70.0
		cart_product = [p for p in Cart.objects.all() if p.user == request.user]
		for p in cart_product:
			tempamount = (p.quantity * p.product.discounted_price)
			# print("Quantity", p.quantity)
			# print("Selling Price", p.product.discounted_price)
			# print("Before", amount)
			amount += tempamount
			# print("After", amount)
		# print("Total", amount)
		data = {
			'quantity':c.quantity,
			'amount':amount,
			'totalamount':amount+shipping_amount
		}
		return JsonResponse(data)
	else:
		return HttpResponse("")

def minus_cart(request):
	if request.method == 'GET':
		prod_id = request.GET['prod_id']
		c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
		c.quantity-=1
		c.save()
		amount = 0.0
		shipping_amount= 70.0
		cart_product = [p for p in Cart.objects.all() if p.user == request.user]
		for p in cart_product:
			tempamount = (p.quantity * p.product.discounted_price)
			# print("Quantity", p.quantity)
			# print("Selling Price", p.product.discounted_price)
			# print("Before", amount)
			amount += tempamount
			# print("After", amount)
		# print("Total", amount)
		data = {
			'quantity':c.quantity,
			'amount':amount,
			'totalamount':amount+shipping_amount
		}
		return JsonResponse(data)
	else:
		return HttpResponse("")

@login_required
def checkout(request):
	user = request.user
	add = Customer.objects.filter(user=user)
	cart_items = Cart.objects.filter(user=request.user)
	amount = 0.0
	shipping_amount = 70.0
	totalamount=0.0
	cart_product = [p for p in Cart.objects.all() if p.user == request.user]
	if cart_product:
		for p in cart_product:
			tempamount = (p.quantity * p.product.discounted_price)
			amount += tempamount
		totalamount = amount+shipping_amount
	return render(request, 'app/checkout.html', {'add':add, 'cart_items':cart_items, 'totalcost':totalamount})

@login_required
def payment_done(request):
	custid = request.GET.get('custid')
	print("Customer ID", custid)
	user = request.user
	cartid = Cart.objects.filter(user = user)
	customer = Customer.objects.get(id=custid)
	print(customer)
	for cid in cartid:
		OrderPlaced(user=user, customer=customer, product=cid.product, quantity=cid.quantity).save()
		print("Order Saved")
		cid.delete()
		print("Cart Item Deleted")
	return redirect("orders")

def remove_cart(request):
	if request.method == 'GET':
		prod_id = request.GET['prod_id']
		c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
		c.delete()
		amount = 0.0
		shipping_amount= 70.0
		cart_product = [p for p in Cart.objects.all() if p.user == request.user]
		for p in cart_product:
			tempamount = (p.quantity * p.product.discounted_price)
			# print("Quantity", p.quantity)
			# print("Selling Price", p.product.discounted_price)
			# print("Before", amount)
			amount += tempamount
			# print("After", amount)
		# print("Total", amount)
		data = {
			'amount':amount,
			'totalamount':amount+shipping_amount
		}
		return JsonResponse(data)
	else:
		return HttpResponse("")

@login_required
def address(request):
	totalitem = 0
	if request.user.is_authenticated:
		totalitem = len(Cart.objects.filter(user=request.user))
	add = Customer.objects.filter(user=request.user)
	return render(request, 'app/address.html', {'add':add, 'active':'btn-primary', 'totalitem':totalitem})

@login_required
def orders(request):
	op = OrderPlaced.objects.filter(user=request.user)
	return render(request, 'app/orders.html', {'order_placed':op})

def fertilizer(request, data=None):
	totalitem = 0
	if request.user.is_authenticated:
		totalitem = len(Cart.objects.filter(user=request.user))
	if data==None :
			fertilizers = Product.objects.filter(category='F')
	elif data == 'Mahadhan' or data == 'Bulk':
			fertilizers = Product.objects.filter(category='F').filter(brand=data)
	elif data == 'below':
			fertilizers = Product.objects.filter(category='F').filter(discounted_price__lt=2000)
	elif data == 'above':
			fertilizers = Product.objects.filter(category='F').filter(discounted_price__gt=2000)
	return render(request, 'app/fertilizer.html', {'fertilizers':fertilizers, 'totalitem':totalitem})
	#create
def pesticide(request, data=None):
	totalitem = 0
	if request.user.is_authenticated:
		totalitem = len(Cart.objects.filter(user=request.user))
	if data==None :
			pesticides = Product.objects.filter(category='P')
	elif data == 'Herbicides' or data == 'Fungicides'or data == 'Insecticides':
			pesticides = Product.objects.filter(category='P').filter(brand=data)
	elif data == 'below':
			pesticides = Product.objects.filter(category='P').filter(discounted_price__lt=2000)
	elif data == 'above':
			pesticides = Product.objects.filter(category='P').filter(discounted_price__gt=2000)
	return render(request, 'app/pesticide.html', {'pesticides':pesticides, 'totalitem':totalitem})
	# create
def seed(request, data=None):
	totalitem = 0
	if request.user.is_authenticated:
		totalitem = len(Cart.objects.filter(user=request.user))
	if data==None :
			seeds = Product.objects.filter(category='S')
	elif data == 'Bollgard2' or data == 'Iris':
			seeds = Product.objects.filter(category='S').filter(brand=data)
	elif data == 'below':
			seeds = Product.objects.filter(category='S').filter(discounted_price__lt=2000)
	elif data == 'above':
			seeds = Product.objects.filter(category='S').filter(discounted_price__gt=2000)
	return render(request, 'app/seed.html', {'seeds':seeds, 'totalitem':totalitem})
# create
def splinker(request, data=None):
	totalitem = 0
	if request.user.is_authenticated:
		totalitem = len(Cart.objects.filter(user=request.user))
	if data==None :
			splinkers = Product.objects.filter(category='SP')
	elif data == 'Pep' or data == 'Jain':
			splinkers = Product.objects.filter(category='SP').filter(brand=data)
	elif data == 'below':
			splinkers = Product.objects.filter(category='SP').filter(discounted_price__lt=2000)
	elif data == 'above':
			splinkers = Product.objects.filter(category='SP').filter(discounted_price__gt=2000)
	return render(request, 'app/splinker.html', {'splinkers':splinkers, 'totalitem':totalitem})

class CustomerRegistrationView(View):
 def get(self, request):
  form = CustomerRegistrationForm()
  return render(request, 'app/customerregistration.html', {'form':form})
  
 def post(self, request):
  form = CustomerRegistrationForm(request.POST)
  if form.is_valid():
   messages.success(request, 'Congratulations!! Registered Successfully.')
   form.save()
  return render(request, 'app/customerregistration.html', {'form':form})

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
	def get(self, request):
		totalitem = 0
		if request.user.is_authenticated:
			totalitem = len(Cart.objects.filter(user=request.user))
		form = CustomerProfileForm()
		return render(request, 'app/profile.html', {'form':form, 'active':'btn-primary', 'totalitem':totalitem})
		
	def post(self, request):
		totalitem = 0
		if request.user.is_authenticated:
			totalitem = len(Cart.objects.filter(user=request.user))
		form = CustomerProfileForm(request.POST)
		if form.is_valid():
			usr = request.user
			name  = form.cleaned_data['name']
			locality = form.cleaned_data['locality']
			city = form.cleaned_data['city']
			state = form.cleaned_data['state']
			zipcode = form.cleaned_data['zipcode']
			reg = Customer(user=usr, name=name, locality=locality, city=city, state=state, zipcode=zipcode)
			reg.save()
			messages.success(request, 'Congratulations!! Profile Updated Successfully.')
		return render(request, 'app/profile.html', {'form':form, 'active':'btn-primary', 'totalitem':totalitem})

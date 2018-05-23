# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse
import requests
import json
from django.http import HttpResponse
from django.http import JsonResponse
from babel.numbers import format_number
import uuid


context={'site_name_ru':'СкамАвиа.ru',
         'site_name': 'scamavia.ru'}

fake_discount=23

def main(request):
	return render_to_response('main.html', context)


def get_data(url, params=None):
	agent='Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'
	headers = {
		'User-Agent': agent
	}

	r = requests.get(url, params=params, headers=headers)
	res = json.loads(r.text)
	return res

def get_seats_word(seats):
	if not seats:
	 return 'xxxx'

	if seats == 1:
		seats_word = 'место'

	if seats == 2 or seats == 3 or seats == 4:
		seats_word = 'места'

	if seats > 4:
		seats_word = 'мест'

	return seats_word

def get_class_word(class_code):
	class_codes_arr={'e' : 'Эконом',
	                'E': 'Эконом',
	                'B': 'Бизнес',
	                'b': 'Бизнес',
	                }
	return class_codes_arr[class_code]

def procc_flight(flight, request):
	currency = request.GET.get('currency', 'RUR')

	seats = 100
	routes = []
	for curr_route in flight['segments_direction']:
		route = {}

		route_segments = []

		total_mins = 0

		for cc in curr_route:

			segment = flight['segments'][cc]
			route_segments.append(flight['segments'][cc])

			if segment['first']:
				route['dep'] = segment['dep']
				route['carrier'] = segment['carrier']
				route['aircraft'] = segment['aircraft']
				route['flight_number'] = segment['flight_number']

			if segment['last']:
				route['arr'] = segment['arr']

			if segment['seats'] < seats:
				seats = segment['seats']

			segment['seats_word'] = get_seats_word(segment['seats'])

			total_mins += segment['duration']['flight']['common']

			if segment['duration'].has_key('transfer'):
				total_mins += segment['duration']['transfer']['common']

			hours = int(total_mins / 60.00)
			mins = total_mins - (hours * 60)
			route['duration'] = {'hour': hours, 'minute': mins}

		route['segments'] = route_segments
		route['id'] = uuid.uuid4()

		if len(route_segments) > 1:
			trc = len(route_segments) - 1
			route['transfers_count'] = trc
			route['transfers_word'] = u'пересадки'

			if trc == 1:
				route['transfers_word'] = u'пересадка'

		routes.append(route)

	flight['routes'] = routes

	if currency == 'RUR':
		currency = 'RUB'

	price = flight['price'][currency]['amount']
	price = price - (price / 100 * fake_discount)
	price = int(price)

	currency_dict = {
		'RUR': 'руб',
		'RUB': 'руб',
		'UAH': 'грн',
		'EUR': '€',
		'USD': '$',
	}

	flight['my_price'] = format_number(price, locale='ru')
	flight['my_price_word'] = currency_dict[currency]

	if seats:
		seats_word = get_seats_word(seats)

		if seats > 9:
			seats = '9+'
		else:
			seats = 'Осталось %d' % seats

		flight['seats'] = seats + ' ' + seats_word

	return flight

def search(request):
	lang = request.GET.get('locale')[:2]

	data = {#'segments[0][from]': request.GET.get('segments[0][from]'),
	        #'segments[0][to]': request.GET.get('segments[0][to]'),
	        #'segments[0][date]': request.GET.get('segments[0][date]'),

	        'adt': request.GET.get('adult'),
	        'chd': request.GET.get('child'),
	        'inf': request.GET.get('infant'),

	        'class': request.GET.get('service_class')[0],

	        'client_key': request.GET.get('client_key'),
	        'lang': lang,

	        'getparams[utm_source]': request.GET.get('utm_source'),

	        }

	for curr in request.GET:
		if curr.startswith('segments['):
			data[curr]=request.GET.get(curr)

	res = get_data('https://api4.aviakassa.ru/v4/avia/search', params=data)

	if not bool(res['success']):
		return HttpResponse(res['data']['message'], status=503)

	sro = res['data']['sro']
	res = get_data('https://api4.aviakassa.ru/v4/avia/search-result', params={'sro': sro, 'lang': lang})

	#Service variables
	#"code": 0,
	#"pid": "130374_591348cd40e48",
	#"success": true,

	res=res['data']
	context.update(res)


	res['search']['class_word']  = get_class_word(res['search']['class'])
	for flight in res['flights']:
		flight=procc_flight(flight, request)

	#return JsonResponse(res)
	return render(request, 'search.html', context)

def booking(request):
	tid = request.GET.get('tid')
	#res = get_data('https://api4.aviakassa.ru/v4/avia/flight-info?tid=%s&fast=1&lang=ru' % tid)
#	res = res['data']
#	context.update(res)

	#res['flight']=procc_flight(res['flight'], request)


	#return JsonResponse(res)
	return render(request, 'book.html', context)



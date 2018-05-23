from django import template

register = template.Library()

@register.inclusion_tag('routes.html')
def gen_routes(flight):
	print flight
	return {'flight': flight}

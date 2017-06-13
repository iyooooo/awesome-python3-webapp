#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Rex'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio

import markdown2

from aiohttp import web

from coroweb import get, post
from models import User, Comment, Blog, next_id

from apis import APIValueError, Page
from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 =re.compile(r'^[0-9a-f]{40}$')

def check_admin(request):
	if request.__user__ is None or not request.__user__.admin:
		raise APIPermissionError()

def get_page_index(page_str):
	p = 1
	try:
		p = int(page_str)
	except ValueError as e:
		pass
	if p < 1:
		p = 1
	return p

def text2html(text):
	lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt')
		, filter(lambda s: s.strip() !='', text.split('\n')))
	return ''.join(lines)

# 加密cookie
def user2cookie(user, max_age):
	'''
	Genarate cookie str by user
	'''

	# build cookie string by: id-expires-sha1
	expires = str(int(time.time() + max_age))
	s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
	L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
	return '_'.join(L)

# 解密cookie
@asyncio.coroutine
def cookie2user(cookie_str):
	'''
	Parse cookie and load user if cookie is valid
	'''
	if not cookie_str:
		return None
	try:
		L = cookie_str.split('_')
		if len(L) != 3:
			return None
		uid, expires, sha1 = L
		if int(expires) < time.time():
			return None
		user = yield from User.find(uid)
		# logging.info('cookie2user ************* %s' % user)
		if user is None:
			return None
		s = '%s-%s-%s-%s' % (uid,user.passwd,expires,_COOKIE_KEY)
		if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
			logging.info('invalid sha1')
			return None
		user.passwd = '******'
		return user
	except Exception as e:
		logging.exception(e)
		return None

@get('/')
def index(request, *, page='1'):

	page_index = get_page_index(page)
	num = yield from Blog.findNumber('count(id)')
	page = Page(num, page_index)
	if num == 0:
		blogs = []
	else:
		# logging.info('page---------------->%s %s'  %(page.offset, page.limit))
		blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
	return {
		'__template__': 'blogs.html',
		'page': page,
		'blogs': blogs,
		'__user__': request.__user__
	}

@get('/register')
def register():
	return {'__template__':'register.html'}

@post('/api/users')
def api_resister_user(*, email, name, passwd):
	if not name or not name.strip():
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not passwd: #or not _RE_SHA1.match(passwd)
		raise APIValueError('passwd')
	users = yield from User.findAll('email=?', [email])
	if len(users) > 0:
		user = users[0]
		u = User(id=user.id)
		yield from u.remove()

		# raise APIError('register:failed', 'email', 'Email is already in use.')
	uid = next_id()
	sha1_passwd = '%s:%s' % (uid, passwd)
	user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), 
				image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
	yield from user.save()
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user,86400), max_age=86400, httponly=True)
	user.passwd = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return r

@post('/api/authenticate')
def authenticate(*, email, passwd):
	# logging.info('authenticate ********* %s %s' %(email,passwd))
	if not email:
		raise APIValueError('email', 'Ivalid email.')
	if not passwd:
		raise APIValueError('passwd', 'Invalid password.')
	users = yield from User.findAll('email=?',[email])
	if len(users) == 0:
		raise APIValueError('email', 'Email not exist.')
	user = users[0]
	# check passwd
	sha1 = hashlib.sha1()
	sha1.update(user.id.encode('utf-8'))
	sha1.update(b':')
	sha1.update(passwd.encode('utf-8'))
	if user.passwd != sha1.hexdigest():
		raise APIValueError('passwd', 'Invalid Password.')
	# authenticate ok, set cookie
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
	user.passwd = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return r

@get('/signin')
def signin():
	return {'__template__': 'signin.html'}

@get('/signout')
def signout(request):
	referer = request.headers.get('Referer')
	# logging.info('signout ---------------------- > %s' % referer)
	r = web.HTTPFound('/')
	r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
	logging.info('user signed out.')
	return r

# REST API
@get('/manage/blogs/create')
def manage_create_blog(request):
	return {
		'__template__': 'manage_blog_edit.html',
		'id': '',
		'action': '/api/blogs',
		'__user__': request.__user__
	}

@post('/api/blogs')
def api_create_blog(request, *, name, summary, content):
	check_admin(request)
	if not name or not name.strip():
		raise APIValueError('name', 'name cannot be empty.')
	if not summary or not summary.strip():
		raise APIValueError('summary', 'summary cannot be empty.')
	if not content or not content.strip():
		raise APIValueError('content', 'content cannot be empty.')
	blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, 
		name=name.strip(), summary=summary.strip(), content=content.strip())
	yield from blog.save()
	logging.info('api_create_blog-------->  %s\n ' % blog)
	return blog

@get('/blog/{id}')
def get_blog(request, *, id, page=1):
	blog = yield from Blog.find(id)
	comments = yield from Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
	for c in comments:
		c.html_content = text2html(c.content)
	blog.html_content =  markdown2.markdown(blog.content)
	return {
		'__template__': 'blog.html',
		'blog': blog,
		'comments': comments,
		'__user__': request.__user__
	}

@get('/api/blogs/{id}')
def api_get_blog(*, id):
	blog = yield from Blog.find(id)
	logging.info('api_get_blog-------->  %s\n ' % blog)
	return blog

# day-12
@get('/api/blogs')
def api_blogs(*, page='1'):
	page_index = get_page_index(page)
	num = yield from Blog.findNumber('count(id)')
	p = Page(num, page_index)
	if num == 0:
		return dict(page=p, blogs=())
	blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
	logging.info(len(blogs))
	return dict(page=p, blogs=blogs)

@get('/manage/blogs')
def manage_blogs(request, *, page='1'):
	return {
		'__template__': 'manage_blogs.html',
		'page_index': get_page_index(page),
		'__user__': request.__user__
	}
	
@get('/manage/blogs/edit')
def manage_edit_blog(request, *, id):
	return {
		'__template__': 'manage_blog_edit.html',
		'id': id,
		'__user__': request.__user__,
		'action': '/api/blogs/%s' % id
	}

@post('/api/blogs/{id}')
def api_edit_blog(request, *, id, name, summary, content):
	check_admin(request)
	blog = yield from Blog.find(id)
	if not name or not name.strip():
		raise APIValueError('name', 'name cannot be empty.')
	if not summary or not summary.strip():
		raise APIValueError('summary', 'name cannot be empty')
	if not content or not content.strip():
		raise APIValueError('content', 'content cannot be empty')
	blog.name = name
	blog.summary = summary
	blog.content = content
	yield from blog.update()
	return blog

@post('/api/blogs/{id}/delete')
def api_delete_blog(request, *, id):
	check_admin(request)
	blog = yield from Blog.find(id)
	yield from blog.remove()
	return dict(id=id)

# day-14
@post('/api/blogs/{id}/comments')
def api_create_comment(id, request, *, content):
	logging.info('api_create_comment-------------> %s %s ' % (id, content))
	user = request.__user__
	if user is None:
		raise APIPermissionError('Please signin first.')
	if not content or not content.strip():
		raise APIValueError('content')
	blog = yield from Blog.find(id)
	if blog is None:
		pass
		# raise APIResourceNotFoundError('Blog')
	comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image, content=content.strip())
	yield from comment.save()
	return comment

@get('/manage/comments')
def manage_comments(request, *, page=1):
	return {
		'__template__': 'manage_comments.html',
		'page_index': get_page_index(page),
		'__user__': request.__user__
	}

@get('/api/comments')
def api_comments(*, page=1):
	page_index = get_page_index(page)
	num = yield from Comment.findNumber('count(id)')
	p = Page(num, page_index)
	if num == 0:
		return dict(page=p, comments=())
	comments = yield from Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
	return dict(page=p, comments=comments)

@post('/api/comments/{id}/delete')
def api_delete_comment(request, *, id):
	check_admin(request)
	comment = yield from Comment.find(id)
	yield from comment.remove()
	return dict(id=id)

@get('/manage/users')
def manage_users(request, *, page=1):
	return {
		'__template__': 'manage_users.html',
		'page_index': get_page_index(page),
		'__user__': request.__user__
	}

@get('/api/users')
def api_users(*, page=1):
	page_index = get_page_index(page)
	num = yield from User.findNumber('count(id)')
	p = Page(num, page_index)
	if num == 0:
		return dict(page=p, users=())
	users = yield from User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
	return dict(page=p, users=users)

@post('/api/users/{id}/delete')
def api_delete_user(request, *, id):
	check_admin(request)
	user = yield from User.find(id)
	yield from user.remove()
	return dict(id=id)

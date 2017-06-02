from models import User, Blog, Comment
import orm

import asyncio

loop = asyncio.get_event_loop()

def test():
	
	'''
	insert  -- ok
	'''
	# yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
	# u = User(name='Test_7', email='test_7@example.com', passwd='1234567890', image='about:blank')
	# yield from u.save()
	# yield from orm.destory_pool()

	'''
	delete  -- ok
	'''
	# yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
	# u = User(id='001495608427965afcba912a1f74f54b5ca7124e673898b000')
	# yield from u.remove()
	# yield from orm.destory_pool()

	'''
	update -- ok
	'''
	# yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
	# u = User(id='00149636444378763e76bca89ea415ebdf32ef4feb6562f000', email='test_*******@example.com', name='Test_0',passwd='12659', admin=False, image='sdasd', created_at='1496364443.78769')
	# yield from u.update()
	# yield from orm.destory_pool()

	'''
	find -- ok
	'''
	# yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
	# u = yield from User.find('00149636444378763e76bca89ea415ebdf32ef4feb6562f000')
	# print('find --------->',u.email)
	# yield from orm.destory_pool()

	'''
	findNum -- ok
	'''
	# yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
	# num = yield from User.findNumber('email')
	# print('findNumber --------->',num)
	# yield from orm.destory_pool()

	'''
	findAll -- ok
	'''
	# yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
	# all = yield from User.findAll()
	# print('findAll --------->',all)
	# yield from orm.destory_pool()

loop.run_until_complete(test())
loop.close()



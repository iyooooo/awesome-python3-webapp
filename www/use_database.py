from models import User, Blog, Comment
import orm

import asyncio

loop = asyncio.get_event_loop()

def test():
	for x in range(4,10000):
		yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
		u = User(name='Test_00%s' % x, email='test_00%s@example.com' % x, passwd='1234567890', image='about:blank')
		yield from u.save()
		yield from orm.destory_pool()

loop.run_until_complete(test())
loop.close()
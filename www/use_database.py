from models import User, Blog, Comment
import orm

import asyncio

loop = asyncio.get_event_loop()

def test():
	yield from orm.create_pool(loop=loop, user='root', password='password', database='awesome')
	u = User(name='Test_009999', email='test_009999@example.com', passwd='1234567890', image='about:blank')
	yield from u.save()
	yield from orm.destory_pool()
		

loop.run_until_complete(test())
loop.close()